import os
import pdfplumber
import re
import json

def extract_text_from_pdf(file_path):
    """Extract full text from a PDF resume."""
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text.strip()

def parse_resume(file_path):
    """Parse resume and extract structured data + full text."""
    text = extract_text_from_pdf(file_path)
    text_clean = text.lower()

    # Extract candidate name (first non-empty line assumption)
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    name = lines[0] if lines else "Unknown"

    # Education keywords
    if "phd" in text_clean:
        education = "PhD"
    elif "master" in text_clean or "m.sc" in text_clean:
        education = "Masters"
    elif "bachelor" in text_clean or "b.tech" in text_clean or "b.sc" in text_clean:
        education = "Bachelors"
    elif "diploma" in text_clean:
        education = "Diploma"
    else:
        education = ""

    # Experience extraction
    exp_match = re.search(r'(\d+)\s*(?:year|yr)', text_clean)
    experience = exp_match.group(1) if exp_match else "0"

    # Skills (basic comma/keyword detection)
    skills_section = re.findall(r'skills[:\-–]?(.*)', text, re.IGNORECASE)
    skills = skills_section[0] if skills_section else ""
    skills = skills.strip() or "Not specified"

    # Projects (optional)
    proj_section = re.findall(r'project[s]?:?(.*)', text, re.IGNORECASE)
    projects = proj_section[0] if proj_section else ""

    parsed_data = {
        "name": name,
        "education": education,
        "experience": experience,
        "skills": skills,
        "projects": projects,
        "text": text  # 🔥 full resume text for semantic similarity
    }

    return parsed_data


def parse_all_resumes(input_folder, output_folder):
    """Parse all PDF resumes and save as JSONs."""
    os.makedirs(output_folder, exist_ok=True)
    parsed_results = []

    for file in os.listdir(input_folder):
        if file.endswith(".pdf"):
            file_path = os.path.join(input_folder, file)
            parsed = parse_resume(file_path)
            output_file = os.path.join(output_folder, file.replace(".pdf", ".json"))

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(parsed, f, indent=4)

            parsed_results.append(parsed)
            print(f"✅ Parsed {file}")

    return parsed_results
