from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
import os
import uuid
from werkzeug.utils import secure_filename
from utils.resume_parser import process_resume, match_resume_with_job, generate_improved_resume
from extensions import mongo

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
            return jsonify({"error": "No resume file uploaded."}), 400

        file = request.files["resume"]
        job_description = request.form.get("jobDescription", "")

        if file.filename == "":
            return jsonify({"error": "No selected file."}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": "Invalid file type. Upload PDF or DOCX."}), 400

        # ✅ Fix file size check
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        if file_size > MAX_FILE_SIZE:
            return jsonify({"error": "File size exceeds the maximum limit of 5MB."}), 400

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

            return render_template("result.html", resume_text=resume_text, analysis=analysis_result, download_link=improved_resume_path)
        except Exception as e:
            return jsonify({"error": f"Error processing resume: {str(e)}"}), 500
