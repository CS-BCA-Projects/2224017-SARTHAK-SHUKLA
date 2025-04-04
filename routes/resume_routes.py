from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
import os
import uuid
from werkzeug.utils import secure_filename
from utils.resume_parser import process_resume, match_resume_with_job, generate_improved_resume
from extensions import mongo
from markupsafe import escape
from flask_wtf.csrf import generate_csrf

resume_bp = Blueprint('resume', __name__)

# Configuration
UPLOAD_FOLDER = "uploads"
RESUME_FOLDER = "static/resumes"
ALLOWED_EXTENSIONS = {"pdf", "docx"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Ensure folders exist
for folder in [UPLOAD_FOLDER, RESUME_FOLDER]:
    os.makedirs(folder, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[-1].lower() in ALLOWED_EXTENSIONS

@resume_bp.route('/dashboard', methods=["GET", "POST"])
@login_required
def dashboard():
    if request.method == "POST":
        # Check if resume file is included
        if "resume" not in request.files:
            flash("No resume file uploaded.", "danger")
            return redirect(url_for("resume.dashboard"))

        file = request.files["resume"]
        job_description = request.form.get("jobDescription", "")

        if file.filename == "":
            flash("No selected file.", "danger")
            return redirect(url_for("resume.dashboard"))

        if not allowed_file(file.filename):
            flash("Invalid file type. Upload PDF or DOCX.", "danger")
            return redirect(url_for("resume.dashboard"))

        # File size check
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        if file_size > MAX_FILE_SIZE:
            flash("File size exceeds the 5MB limit.", "danger")
            return redirect(url_for("resume.dashboard"))

        # Save file
        filename = str(uuid.uuid4()) + "_" + secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        try:
            # Resume processing
            resume_text = process_resume(file_path)
            analysis_result = match_resume_with_job(resume_text, job_description)
            match_percentage = analysis_result.get("match_percentage", 0)
            feedback = escape(analysis_result.get("feedback", "No feedback available."))

            # Generate improved resume
            improved_filename = f"improved_{uuid.uuid4()}.docx"
            improved_resume_path = os.path.join(RESUME_FOLDER, improved_filename)
            generate_improved_resume(resume_text, analysis_result, improved_resume_path)

            flash("Resume uploaded and analyzed successfully!", "success")
            return render_template(
                "result.html",
                resume_text=resume_text,
                match_percentage=match_percentage,
                feedback=feedback,
                download_filename=improved_filename
            )

        except Exception as e:
            flash(f"Error processing resume: {str(e)}", "danger")
            return redirect(url_for("resume.dashboard"))

    # Render dashboard with CSRF token
    return render_template(
        "dashboard.html",
        username=current_user.username,
        csrf_token=generate_csrf()
    )

@resume_bp.route("/download/<filename>")
@login_required
def download_resume(filename):
    file_path = os.path.join(RESUME_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        flash("File not found!", "danger")
        return redirect(url_for("resume.dashboard"))
