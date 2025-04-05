import docx2txt
import PyPDF2
import google.generativeai as genai
import os
import re
import time
from dotenv import load_dotenv
from docx import Document
from docx.shared import RGBColor, Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from config import GEMINI_MODEL
import logging

# 🧠 Load Environment Variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# 📝 Logging Setup
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# =====================================
# 🧠 Gemini API Call
# =====================================
def call_gemini(prompt, retries=3):
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        logging.debug("🔍 Gemini Response: %s", response.text)
        return response.text.strip() if response and hasattr(response, "text") else "Error: No response from Gemini."
    except Exception as e:
        if retries > 0:
            time.sleep(2)  # Retry mechanism with delay
            return call_gemini(prompt, retries - 1)
        logging.error("Error calling Gemini API: %s", str(e))
        return f"Error calling Gemini API: {str(e)}"

# =====================================
# 📄 Resume File Text Extraction
# =====================================
def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                extracted_text = page.extract_text()
                if extracted_text:
                    text += extracted_text + "\n"
    except Exception as e:
        logging.error("Error extracting text from PDF: %s", str(e))
        return f"Error extracting text from PDF: {str(e)}"
    return text.strip()

def extract_text_from_docx(docx_path):
    try:
        return docx2txt.process(docx_path).strip()
    except Exception as e:
        logging.error("Error extracting text from DOCX: %s", str(e))
        return f"Error extracting text from DOCX: {str(e)}"

def process_resume(file_path):
    if file_path.endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    elif file_path.endswith(".docx"):
        return extract_text_from_docx(file_path)
    else:
        return "Unsupported file format. Please upload a PDF or DOCX file."

# =====================================
# 📝 Feedback Formatting
# =====================================


def format_feedback(raw_feedback):
    formatted_feedback = raw_feedback.strip()

    # Handle bold text: Convert Markdown-style **bold** to HTML <strong>
    formatted_feedback = re.sub(r'\*\*(.*?)\*\*', r'', formatted_feedback)

    # Ensure any double newlines are replaced by a single newline for better spacing between sections
    formatted_feedback = re.sub(r'\n{2,}', '\n\n', formatted_feedback)

    # Add section headers with <h3> tags for Strengths, Missing Skills, Areas for Improvement
    formatted_feedback = formatted_feedback.replace("Strengths:", "Strengths:")
    formatted_feedback = formatted_feedback.replace("Missing Skills:", "Missing Skills:")
    formatted_feedback = formatted_feedback.replace("Areas for Improvement:", "Areas for Improvement:")

    # Handle list items marked with - or symbols like ❌ and ⚠️
    formatted_feedback = re.sub(r'(\n[❌⚠️].*)', r'<p>\1</p>', formatted_feedback)

    # Wrap list items within <ul><li> tags, ensuring only the list items are wrapped
    formatted_feedback = re.sub(r'<p>([❌⚠️].*)</p>', r'<ul><li>\1</li></ul>', formatted_feedback)

    # Clean up unintended nested <ul><ul> tags
    formatted_feedback = re.sub(r'</ul><ul>', '', formatted_feedback)

    # Further cleanup to remove <p> tags around individual list items if needed
    formatted_feedback = re.sub(r'<ul><li><p>(.*?)</p></li></ul>', r'<ul><li>\1</li></ul>', formatted_feedback)

    return formatted_feedback


# =====================================
# 🎯 Skill Extraction from Gemini Feedback
# =====================================
def extract_skills_from_feedback(feedback, section):
    try:
        pattern = rf"{section}:\n((?:- .+\n?)+)"
        matches = re.search(pattern, feedback, re.IGNORECASE)
        if matches:
            return [line.strip("- ").strip() for line in matches.group(1).strip().splitlines()]
        return []
    except Exception as e:
        logging.error("Error extracting %s: %s", section, str(e))
        return []

# =====================================
# 🧠 Match Resume with Job Description
# =====================================
def match_resume_with_job(resume_text, job_description):
    try:
        prompt = f"""
You are an expert career advisor and resume evaluator.

Your task is to analyze the candidate's resume in comparison with the given job description and return a structured report.

⚠️ Strictly follow the format below. Do NOT add anything else.

FORMAT TO FOLLOW:
Match Score: [X]%

Missing Skills:
- List technical and soft skills that are relevant to the job but not present in the resume.

Strengths:
- Highlight skills, projects, or experiences from the resume that match well with the job description.

Areas for Improvement:
- Provide specific suggestions to align the resume better with the job role, such as skills to add, formatting tips, or ways to reword existing content.

===========================

📄 Resume:
{resume_text}

📝 Job Description:
{job_description}
"""
        response = call_gemini(prompt)
        logging.debug("🔍 Gemini Full Response: %s", response)

        if "Match Score" not in response:
            return {
                "match_percentage": 0,
                "feedback": "⚠️ Gemini failed to return structured feedback. Please try again.\n\nRaw Response:\n" + response,
                "matched_skills": [],
                "missing_skills": []
            }

        match_score = re.search(r"Match Score: (\d+)%", response)
        if match_score:
            match_percentage = int(match_score.group(1))
        else:
            raise ValueError("Match Score not found in response.")

        matched_skills = extract_skills_from_feedback(response, "Strengths")
        missing_skills = extract_skills_from_feedback(response, "Missing Skills")

        return {
            "match_percentage": match_percentage,
            "feedback": format_feedback(response),
            "matched_skills": matched_skills,
            "missing_skills": missing_skills
        }

    except Exception as e:
        logging.error("Error processing Gemini response: %s", str(e))
        return {
            "match_percentage": 0,
            "feedback": f"⚠️ Error processing Gemini response: {str(e)}",
            "matched_skills": [],
            "missing_skills": []
        }

# =====================================
# 📝 Generate Improved Resume
# =====================================
def generate_improved_resume(resume_text, analysis_result, output_path):
    improved_text = call_gemini(f"""
Based on the following resume and analysis feedback, generate an improved version:

Resume:
{resume_text}

Analysis Feedback:
{analysis_result}

Format it as a single-column layout using this structure:
📌 **Professional Summary**
🛠️ **Skills**
💼 **Experience**
🎓 **Education**
📜 **Certifications** (if any)

Use bullet points, emoji markers, and keep the tone professional.
Quantify achievements and improve readability. Keep it stylish, clean, and modern.
""")

    # 📝 Create Word Document
    doc = Document()

    # 📌 Title
    title = doc.add_heading("\U0001F4BC Improved Resume", level=1)
    title.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

    sections = ["Professional Summary", "Skills", "Experience", "Education", "Certifications"]

    for paragraph in improved_text.split("\n\n"):
        lines = paragraph.strip().split("\n")
        if not lines:
            continue

        first_line = lines[0].strip()
        section_match = next((sec for sec in sections if sec.lower() in first_line.lower()), None)

        if section_match:
            heading = doc.add_paragraph()
            run = heading.add_run(first_line)
            run.bold = True
            run.font.size = Pt(12)
            run.font.color.rgb = RGBColor(0, 102, 204)
            content_lines = lines[1:]
        else:
            content_lines = lines

        for line in content_lines:
            line = line.strip()
            if line.startswith("-") or line.startswith("•"):
                doc.add_paragraph(line.lstrip("-• ").strip(), style='List Bullet')
            elif line:
                para = doc.add_paragraph(line)
                para.paragraph_format.space_after = Pt(6)

    # 💡 Footer Note
    doc.add_paragraph(
        "\n\U0001F4A1 Note: Focus on improving the highlighted target areas and quantify achievements when updating your resume.",
        style="Normal"
    )

    # 💾 Save
    doc.save(output_path)
    return output_path
