from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
import os
import uuid
from werkzeug.utils import secure_filename
from utils.resume_parser import process_resume, match_resume_with_job, generate_improved_resume
from extensions import mongo
from models import User

resume_bp = Blueprint("resume", __name__)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "docx"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[-1].lower() in ALLOWED_EXTENSIONS

@resume_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload_resume():
    if request.method == "POST":
        if "resume" not in request.files:
            flash("No resume file uploaded.", "danger")
            return redirect(url_for("resume.upload_resume"))

        file = request.files["resume"]
        job_description = request.form.get("jobDescription", "")

        if file.filename == "":
            flash("No selected file.", "danger")
            return redirect(url_for("resume.upload_resume"))

        if not allowed_file(file.filename):
            flash("Invalid file type. Upload PDF or DOCX.", "danger")
            return redirect(url_for("resume.upload_resume"))

        # ✅ Fix file size check
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        if file_size > MAX_FILE_SIZE:
            flash("File size exceeds the maximum limit of 5MB.", "danger")
            return redirect(url_for("resume.upload_resume"))

        # ✅ Save with unique filename
        filename = str(uuid.uuid4()) + "_" + secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        try:
            resume_text = process_resume(file_path)
            analysis_result = match_resume_with_job(resume_text, job_description)
            improved_resume_path = generate_improved_resume(resume_text, analysis_result)

            # ✅ Store analysis in MongoDB
            resume_analysis = {
                "user_id": current_user.id,
                "resume_text": resume_text,
                "job_description": job_description,
                "match_score": analysis_result.get("match_percentage", 0),
                "feedback": analysis_result.get("feedback", "")
            }
            mongo.db.resume_analysis.insert_one(resume_analysis)

            flash("Resume uploaded and analyzed successfully!", "success")
            return render_template("result.html", resume_text=resume_text, analysis=analysis_result, download_link=improved_resume_path)
        except Exception as e:
            flash(f"Error processing resume: {str(e)}", "danger")
            return redirect(url_for("resume.upload_resume"))
    
    return render_template("upload_resume.html")  # ✅ Ensure GET request returns a template
