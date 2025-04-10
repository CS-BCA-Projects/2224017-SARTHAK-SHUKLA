from flask import (
    Blueprint, render_template, request, jsonify, redirect,
    url_for, flash, send_file, send_from_directory
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from flask_wtf.csrf import generate_csrf
from markupsafe import escape

import io
import uuid
from datetime import datetime
from bson import ObjectId
import re
import cloudinary.uploader

from utils.resume_parser import (
    process_resume,
    match_resume_with_job,
    generate_improved_resume
)
from extensions import mongo

resume_bp = Blueprint('resume', __name__)

ALLOWED_EXTENSIONS = {"pdf", "docx"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

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

        file.seek(0, io.SEEK_END)
        if file.tell() > MAX_FILE_SIZE:
            flash("File size exceeds the 5MB limit.", "danger")
            return redirect(url_for("resume.dashboard"))
        file.seek(0)

        if not job_description:
            flash("Job description is required.", "danger")
            return redirect(url_for("resume.dashboard"))

        file_stream = io.BytesIO(file.read())
        file.seek(0)

        try:
            # Upload original resume to Cloudinary with timestamped filename
            ext = file.filename.rsplit(".", 1)[1].lower()
            timestamp = int(datetime.utcnow().timestamp())
            public_id = f"original_resumes/original_resume_{timestamp}"

            cloudinary_original = cloudinary.uploader.upload_large(
                file_stream,
                resource_type="raw",
                type="upload",
                access_mode="public",             # Makes file publicly downloadable
                public_id=f"{public_id}.{ext}",
                overwrite=True
            )

            original_url = cloudinary_original.get("secure_url")

            resume_text = process_resume(file)
            analysis_result = match_resume_with_job(resume_text, job_description)

            match_percentage = analysis_result.get("match_percentage", 0)
            feedback = analysis_result.get("feedback", "No feedback available.")
            matched_skills = analysis_result.get("matched_skills", [])
            missing_skills = analysis_result.get("missing_skills", [])
            feedback_dict = parse_feedback(feedback)

            improved_url = generate_improved_resume(resume_text, analysis_result)
            if not improved_url:
                flash("Failed to generate and upload improved resume.", "danger")
                return redirect(url_for("resume.dashboard"))

            improved_filename = improved_url.split("/")[-1]

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
                "resume_filename": f"original_resume_{timestamp}.{ext}",
                "resume_path": original_url,
                "improved_filename": improved_filename,
                "improved_resume_path": improved_url,
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
                original_filename=f"original_resume_{timestamp}.{ext}"
            )

        except Exception as e:
            flash(f"Error processing resume: {str(e)}", "danger")
            return redirect(url_for("resume.dashboard"))

    return render_template(
        "dashboard.html",
        username=current_user.username,
        csrf_token=generate_csrf()
    )

@resume_bp.route("/download/<filename>")
@login_required
def download_resume(filename):
    entry = mongo.db.analysis.find_one({
        "improved_filename": filename,
        "user_id": str(current_user.id)
    })
    if not entry:
        flash("File not found or access denied.", "danger")
        return redirect(url_for("resume.dashboard"))

    return redirect(entry["improved_resume_path"])

@resume_bp.route("/uploads/<filename>")
@login_required
def download_original_resume(filename):
    entry = mongo.db.analysis.find_one({
        "resume_filename": filename,
        "user_id": str(current_user.id)
    })
    if not entry:
        flash("File not found or access denied.", "danger")
        return redirect(url_for("resume.dashboard"))

    return redirect(entry["resume_path"])

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

@resume_bp.route("/view-result/<entry_id>")
@login_required
def view_result(entry_id):
    entry = mongo.db.analysis.find_one({"_id": ObjectId(entry_id), "user_id": str(current_user.id)})

    if not entry:
        flash("Result not found or access denied.", "danger")
        return redirect(url_for("resume.history"))

    feedback_dict = parse_feedback(entry.get("feedback", "No feedback available."))

    return render_template(
        "result.html",
        resume_text="(Original resume text not stored)",
        Name=entry.get("resume_holder_name", "N/A"),
        email=entry.get("resume_holder_email", "N/A"),
        phone=entry.get("resume_holder_phone", "N/A"),
        match_percentage=entry.get("match_percentage", 0),
        feedback=entry.get("feedback", ""),
        feedback_dict=feedback_dict,
        matched_skills=entry.get("matched_skills", []),
        missing_skills=entry.get("missing_skills", []),
        download_filename=entry.get("improved_filename"),
        original_filename=entry.get("resume_filename")
    )

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

    # Delete from Cloudinary
    try:
        if entry.get("resume_filename"):
            cloudinary.uploader.destroy(f"original_resumes/{entry['resume_filename'].rsplit('.', 1)[0]}", resource_type="raw")
        if entry.get("improved_filename"):
            cloudinary.uploader.destroy(f"improved_resumes/{entry['improved_filename'].rsplit('.', 1)[0]}", resource_type="raw")
    except Exception as e:
        flash(f"Error deleting files from Cloudinary: {e}", "warning")

    mongo.db.analysis.delete_one({"_id": ObjectId(entry_id)})
    flash("Entry deleted successfully.", "success")
    return redirect(url_for("resume.history"))