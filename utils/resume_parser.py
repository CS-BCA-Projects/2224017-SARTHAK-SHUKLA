import docx2txt
import PyPDF2
import google.generativeai as genai
import os
import re
from dotenv import load_dotenv
import docx
from docx.shared import RGBColor
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from config import GEMINI_MODEL  # Import model name from config

load_dotenv()
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini client
def call_gemini(prompt):
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        return response.text.strip() if response and hasattr(response, "text") else "Error: No response from Gemini."
    except Exception as e:
        return f"Error calling Gemini API: {str(e)}"

# Extract text from PDF
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
        return f"Error extracting text from PDF: {str(e)}"
    return text.strip()

# Extract text from DOCX
def extract_text_from_docx(docx_path):
    try:
        return docx2txt.process(docx_path).strip()
    except Exception as e:
        return f"Error extracting text from DOCX: {str(e)}"

# Process Resume
def process_resume(file_path):
    if file_path.endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    elif file_path.endswith(".docx"):
        return extract_text_from_docx(file_path)
    return "Unsupported file format"

# Format feedback into HTML for result page
def format_feedback(raw_feedback):
    """
    Cleans the feedback without adding HTML tags so the Jinja template can split and match section titles.
    """
    return raw_feedback.strip()
# Match Resume with Job Description
def match_resume_with_job(resume_text, job_description):
    response = call_gemini(f"""
    Analyze the following resume and compare it to the given job description.
    
    Resume:
    {resume_text}

    Job Description:
    {job_description}

    Provide structured feedback strictly in this format:
    
    Match Score: [X]% (Provide a numeric score based on the resume match)
    
    Missing Skills:
    - List missing technical and soft skills relevant to the job.
    
    Strengths:
    - Highlight key skills and projects that align with the job description.
    
    Areas for Improvement:
    - Suggest specific improvements to align better with the job role.
    
    Keep the response structured and avoid unnecessary explanations.
    """)

    match_score = re.search(r"Match Score: (\d+)%", response)
    match_percentage = int(match_score.group(1)) if match_score else 0

    formatted_feedback = format_feedback(response)

    return {
        "match_percentage": match_percentage,
        "feedback": formatted_feedback
    }

# Generate Improved Resume
def generate_improved_resume(resume_text, analysis_result, output_path):
    improved_text = call_gemini(f"""
    Based on the following resume and analysis feedback, generate an improved version:
    
    Resume:
    {resume_text}
    
    Analysis Feedback:
    {analysis_result}
    
    Structure it in this order:
    1. Professional Summary
    2. Skills
    3. Experience
    4. Education
    5. Certifications (if any)

    Make sure each section is well-formatted, uses bullet points where needed, and uses clear headings.
    """)

    doc = docx.Document()

    # Title
    title = doc.add_heading("Improved Resume", level=1)
    title.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

    # Define known section headers
    sections = ["Professional Summary", "Skills", "Experience", "Education", "Certifications"]
    section_found = None

    for paragraph in improved_text.split("\n\n"):
        lines = paragraph.strip().split("\n")
        if not lines:
            continue

        first_line = lines[0].strip()

        # Check if it starts with a known section
        if any(section.lower() in first_line.lower() for section in sections):
            section_found = first_line
            heading = doc.add_paragraph()
            run = heading.add_run(first_line)
            run.bold = True
            run.font.color.rgb = RGBColor(0, 102, 204)
            continue

        # If section is found, add bullets under it
        for line in lines:
            line = line.strip()
            if line.startswith("-") or line.startswith("•"):
                doc.add_paragraph(line.lstrip("-• ").strip(), style='List Bullet')
            elif line:  # Paragraph content
                doc.add_paragraph(line)

    # Save the improved document
    doc.save(output_path)
    return output_path
