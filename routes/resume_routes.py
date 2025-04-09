from flask import (
    Blueprint, render_template, request, jsonify, redirect,
    url_for, flash, send_file, send_from_directory
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from flask_wtf.csrf import generate_csrf
from markupsafe import escape

import os
import uuid
from datetime import datetime
from bson import ObjectId
import re

from utils.resume_parser import (
    process_resume,
    match_resume_with_job,
    generate_improved_resume
)
from extensions import mongo

resume_bp = Blueprint('resume', __name__)

# Configuration
UPLOAD_FOLDER = "uploads"
RESUME_FOLDER = "static/resumes"
ALLOWED_EXTENSIONS = {"pdf", "docx"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESUME_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_feedback(feedback):
    sections = ['Strengths', 'Missing Skills', 'Areas for Improvement']
    result = {section: [] for section in sections}

    clean_feedback = feedback.strip().replace('\r\n', '\n')
    pattern = r'(?P<section>Strengths|Missing Skills|Areas for Improvement):\s*\n'
    parts = re.split(pattern, clean_feedback, flags=re.IGNORECASE)

    for i in range(1, len(parts), 2):
        section_title = parts[i].strip().title()
        content = parts[i + 1].strip()
        items = [
            line.strip('- ').strip()
            for line in content.splitlines()
            if line.strip() and (line.strip().startswith('-') or len(line.strip()) > 0)
        ]
        result[section_title] = items

    return result

@resume_bp.route('/dashboard', methods=["GET", "POST"])
@login_required
def dashboard():
    if request.method == "POST":
        file = request.files.get("resume")
        job_description = request.form.get("jobDescription", "").strip()

        if not file or file.filename == "":
            flash("No resume file uploaded.", "danger")
            return redirect(url_for("resume.dashboard"))

        if not allowed_file(file.filename):
            flash("Invalid file type. Please upload a PDF or DOCX file.", "danger")
            return redirect(url_for("resume.dashboard"))

        file.seek(0, os.SEEK_END)
        if file.tell() > MAX_FILE_SIZE:
            flash("File size exceeds the 5MB limit.", "danger")
            return redirect(url_for("resume.dashboard"))
        file.seek(0)

        if not job_description:
            flash("Job description is required.", "danger")
            return redirect(url_for("resume.dashboard"))

        original_filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
        original_path = os.path.join(UPLOAD_FOLDER, original_filename)
        file.save(original_path)

        try:
            resume_text = process_resume(original_path)
            analysis_result = match_resume_with_job(resume_text, job_description)

            match_percentage = analysis_result.get("match_percentage", 0)
            feedback = analysis_result.get("feedback", "No feedback available.")
            matched_skills = analysis_result.get("matched_skills", [])
            missing_skills = analysis_result.get("missing_skills", [])
            feedback_dict = parse_feedback(feedback)

            improved_filename = f"improved_{uuid.uuid4()}.docx"
            improved_path = os.path.join(RESUME_FOLDER, improved_filename)
            generate_improved_resume(resume_text, analysis_result, improved_path)

            resume_holder_name = analysis_result.get("Name", "N/A")
            resume_holder_email = analysis_result.get("email", "N/A")
            resume_holder_phone = analysis_result.get("phone", "N/A")

            mongo.db.analysis.insert_one({
                "user_id": current_user.id,
                "username": current_user.username,
                "resume_holder_name": resume_holder_name,
                "resume_holder_email": resume_holder_email,
                "resume_holder_phone": resume_holder_phone,
                "job_description": job_description,
                "match_percentage": match_percentage,
                "feedback": feedback,
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
                "resume_filename": original_filename,
                "resume_path": original_path,
                "improved_filename": improved_filename,
                "improved_resume_path": improved_path,
                "timestamp": datetime.utcnow()
            })

            flash("Resume uploaded and analyzed successfully!", "success")
            return render_template(
                "result.html",
                resume_text=resume_text,
                Name=resume_holder_name,
                email=resume_holder_email,
                phone=resume_holder_phone,
                match_percentage=match_percentage,
                feedback=feedback,
                feedback_dict=feedback_dict,
                matched_skills=matched_skills,
                missing_skills=missing_skills,
                download_filename=improved_filename,
                original_filename=original_filename
            )

        except Exception as e:
            flash(f"Error processing resume: {str(e)}", "danger")
            return redirect(url_for("resume.dashboard"))

    return render_template(
        "dashboard.html",
        username=current_user.username,
        csrf_token=generate_csrf()
    )

# 🔽 For improved resume (still served from static/)
@resume_bp.route("/download/<filename>")
@login_required
def download_resume(filename):
    file_path = os.path.join(RESUME_FOLDER, secure_filename(filename))
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        flash("File not found!", "danger")
        return redirect(url_for("resume.dashboard"))

# 🔽 For original file (served from uploads/)
@resume_bp.route("/uploads/<filename>")
@login_required
def download_original_resume(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

@resume_bp.route('/history')
@login_required
def history():
    user_id = str(current_user.id)
    analysis_data = mongo.db.analysis.find({"user_id": user_id}).sort("timestamp", -1)

    analysis_entries = []
    for entry in analysis_data:
        analysis_entries.append({
            "id": str(entry["_id"]),
            "holder_name": entry.get("resume_holder_name", entry.get("username", "Anonymous")),
            "holder_email": entry.get("resume_holder_email", "N/A"),
            "holder_phone": entry.get("resume_holder_phone", "N/A"),
            "match_percentage": entry.get("match_percentage", 0),
            "job_description": entry.get("job_description", "N/A"),
            "matched_skills": entry.get("matched_skills", []),
            "missing_skills": entry.get("missing_skills", []),
            "timestamp": entry.get("timestamp", datetime.now()),
            "resume_url": url_for("resume.download_original_resume", filename=entry.get("resume_filename", "")),
            "improved_resume_url": url_for("resume.download_resume", filename=entry.get("improved_filename", ""))
        })

    return render_template("history.html", analysis_entries=analysis_entries)

@resume_bp.route("/delete-entry", methods=["POST"])
@login_required
def delete_entry():
    entry_id = request.form.get("entry_id")
    if not entry_id:
        flash("Invalid request.", "danger")
        return redirect(url_for("resume.history"))

    entry = mongo.db.analysis.find_one({"_id": ObjectId(entry_id), "user_id": str(current_user.id)})
    if not entry:
        flash("Entry not found.", "danger")
        return redirect(url_for("resume.history"))

    try:
        resume_path = entry.get("resume_path", "").replace("\\", "/")
        improved_path = entry.get("improved_resume_path", "").replace("\\", "/")

        if resume_path and os.path.exists(resume_path):
            os.remove(resume_path)
        if improved_path and os.path.exists(improved_path):
            os.remove(improved_path)
    except Exception as e:
        flash(f"Error deleting files: {str(e)}", "warning")

    mongo.db.analysis.delete_one({"_id": ObjectId(entry_id)})
    flash("Entry deleted successfully.", "success")
    return redirect(url_for("resume.history"))
