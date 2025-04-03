import google.generativeai as genai
import PyPDF2
from docx.shared import Pt
from docx.oxml import OxmlElement
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx import Document
import os
import logging
import re  # Added for extracting match percentage

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
        return extract_text_from_pdf(file_path)
    elif ext == "docx":
        return extract_text_from_docx(file_path)
    else:
        return "Error: Unsupported file format."

# Set up logging
logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def match_resume_with_job(resume_text, job_description):
    if not resume_text or resume_text.startswith("Error:"):
        return {"error": "Invalid resume text. Please upload a valid resume."}
    if not job_description.strip():
        return {"error": "Job description is missing."}

    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        prompt = f"""
        You are an AI-powered resume analyzer. Generate a structured response using Markdown format:
        
        **## Resume Analysis Report**
        
         **### 0. Match percentage of resume through job description **
         
        **### 1. Missing Skills**  
        - List the key skills missing from the resume in bullet format.
        
        **### 2. Strengths in Resume**  
        - Highlight strengths like relevant experience, technical skills, and achievements.
        
        **### 3. Areas for Improvement**  
        - List weaknesses like formatting issues, vague descriptions, or missing key details.
        
        **### 4. AI-Suggested Resume Rewrite**  
        - Provide a cleaned-up, structured version of the resume with improvements.

        ---
        **Resume Content:**  
        {resume_text}  

        **Job Description:**  
        {job_description}
        ---
        """

        response = model.generate_content(prompt)

        if response and hasattr(response, "text"):
            formatted_feedback = response.text.replace("\n", "<br>")  # Convert new lines for HTML display
            return {"feedback": formatted_feedback}

        return {"error": "No valid response from AI."}

    except Exception as e:
        logger.error(f"Error during resume matching: {str(e)}")
        return {"error": str(e)}


def generate_improved_resume(resume_text, feedback):
    resume_folder = "static/resumes"
    if not os.path.exists(resume_folder):
        os.makedirs(resume_folder)

    file_path = os.path.join(resume_folder, "improved_resume.docx")

    doc = Document()
    doc.add_heading("Updated Resume", level=1)
    doc.add_paragraph(resume_text)
    doc.add_paragraph("\n\n### AI Suggestions:\n")
    doc.add_paragraph(feedback)

    doc.save(file_path)
    print(f" Improved Resume Saved at: {file_path}")
    return file_path
