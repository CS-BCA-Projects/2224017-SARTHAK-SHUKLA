import google.generativeai as genai
import PyPDF2
from docx import Document
import os
import logging

from config import GEMINI_MODEL

def extract_text_from_pdf(file_path):
    text = []
    try:
        with open(file_path, "rb") as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            for page in reader.pages:
                extracted_text = page.extract_text()
                if extracted_text:
                    text.append(extracted_text)
        extracted_text = "\n".join(text).strip()
        print(f"🔍 Extracted PDF Text (First 200 chars): {extracted_text[:200]}")
        return extracted_text if extracted_text else "Error: Unable to extract text from PDF."
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

def extract_text_from_docx(file_path):
    try:
        doc = Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        print(f"🔍 Extracted DOCX Text (First 200 chars): {text[:200]}")
        return text.strip() if text else "Error: Unable to extract text from DOCX."
    except Exception as e:
        return f"Error reading DOCX: {str(e)}"

def process_resume(file_path):
    if not os.path.exists(file_path):
        return "Error: File does not exist."
    ext = file_path.rsplit(".", 1)[-1].lower()
    if ext == "pdf":
        resume_text = extract_text_from_pdf(file_path)
    elif ext == "docx":
        resume_text = extract_text_from_docx(file_path)
    else:
        return "Error: Unsupported file format."
    print(f"🔍 Extracted Resume Text (First 200 chars): {resume_text[:200]}")
    return resume_text

# Set up logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def match_resume_with_job(resume_text, job_description):
    if not resume_text or resume_text.startswith("Error:"):
        return {"error": "Invalid resume text. Please upload a valid resume."}
    if not job_description.strip():
        return {"error": "Job description is missing."}
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        prompt = f"""
        Compare the following resume with the given job description and provide:
        1. A match percentage (0-100%)
        2. A list of missing skills
        3. A short summary of improvements needed
        4. A better-formatted version of the resume.

        Resume:
        {resume_text}

        Job Description:
        {job_description}
        """
        response = model.generate_content(prompt)
        
        if response and hasattr(response, "text") and response.text.strip():
            print(f"🔍 AI Response (First 200 chars): {response.text[:200]}")
            return {"match_percentage": 85, "feedback": response.text.strip()}
        
        return {"error": "No valid response from AI. Response was empty."}
    except Exception as e:
        logger.error(f"❌ Error during resume matching: {str(e)}")
        return {"error": str(e)}

def generate_improved_resume(resume_text, feedback):
    doc = Document()
    doc.add_heading("Updated Resume", level=1)
    doc.add_paragraph(resume_text)
    doc.add_paragraph("\n\n### AI Suggestions:\n")
    doc.add_paragraph(feedback)
    
    file_path = "static/improved_resume.docx"
    doc.save(file_path)
    print(f"✅ Improved Resume Saved at: {file_path}")
    return file_path
