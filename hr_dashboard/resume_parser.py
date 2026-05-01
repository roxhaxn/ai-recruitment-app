import os
import re
from pathlib import Path

try:
    import pdfplumber
except Exception:
    pdfplumber = None

def _read_pdf_text(pdf_path: str) -> str:
    text = ""

    # 1) pdfplumber first
    if pdfplumber is not None:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
        except Exception:
            pass

    # 2) fallback to pypdf (lazy import to avoid startup crash)
    if not text:
        try:
            from pypdf import PdfReader
            reader = PdfReader(pdf_path)
            for page in reader.pages:
                text += page.extract_text() or ""
        except Exception:
            pass

    return text

def parse_resume(pdf_path: str) -> dict:
    if not Path(pdf_path).exists():
        return {"error": "File not found"}

    text = _read_pdf_text(pdf_path)
    if not text.strip():
        return {
            "name": "Unknown Candidate",
            "email": "",
            "phone": "",
            "experience": 0,
            "education": ["Not Specified"],
            "skills": []
        }

    return _extract_fields(text)


def _extract_fields(text: str) -> dict:
    """Extract structured fields from resume text."""
    
    # Name extraction (first line or common pattern)
    name = _extract_name(text)
    
    # Email extraction
    email = _extract_email(text)
    
    # Phone extraction
    phone = _extract_phone(text)
    
    # Experience extraction
    experience = _extract_experience(text)
    
    # Education extraction
    education = _extract_education(text)
    
    # Skills extraction
    skills = _extract_skills(text)
    
    return {
        "name": name,
        "email": email,
        "phone": phone,
        "experience": experience,
        "education": education,
        "skills": skills,
    }


def _extract_name(text: str) -> str:
    """Extract candidate name from resume."""
    lines = text.split('\n')
    for line in lines[:5]:  # Check first 5 lines
        line = line.strip()
        if line and len(line) < 50 and not any(c.isdigit() for c in line):
            return line
    return "Candidate"


def _extract_email(text: str) -> str:
    """Extract email address."""
    emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    return emails[0] if emails else ""


def _extract_phone(text: str) -> str:
    """Extract phone number."""
    phones = re.findall(r'[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}', text)
    return phones[0] if phones else ""


def _extract_experience(text: str) -> int:
    """Extract years of experience."""
    text_lower = text.lower()
    
    # Look for patterns like "X years of experience"
    exp_patterns = [
        r'(\d+)\s*\+?\s*years?\s+(?:of\s+)?experience',
        r'experience:\s*(\d+)\s*years?',
        r'(\d+)\s*years?\s+in\s+',
    ]
    
    for pattern in exp_patterns:
        match = re.search(pattern, text_lower)
        if match:
            return int(match.group(1))
    
    # Count job entries as proxy for experience
    job_keywords = ['experience', 'employment', 'work history']
    if any(kw in text_lower for kw in job_keywords):
        return 2  # Default to 2 years if work section exists
    
    return 0


def _extract_education(text: str) -> list:
    """Extract education qualifications."""
    education = []
    text_lower = text.lower()
    
    degrees = {
        'phd': r'\b(phd|ph\.d|doctorate)\b',
        'masters': r'\b(masters?|m\.tech|mba|m\.s|msc|m\.sc)\b',
        'bachelors': r'\b(bachelor|b\.tech|bsc|b\.sc|ba|bs|engineering)\b',
        'diploma': r'\b(diploma|associate)\b',
    }
    
    for degree_name, pattern in degrees.items():
        if re.search(pattern, text_lower):
            education.append(degree_name.title())
    
    return education if education else ['Not Specified']


def _extract_skills(text: str) -> list:
    """Extract technical and professional skills."""
    text_lower = text.lower()
    
    common_skills = [
        'python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'go', 'rust', 'kotlin',
        'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'cassandra', 'dynamodb',
        'html', 'css', 'react', 'angular', 'vue', 'nodejs', 'express', 'django', 'flask', 'spring',
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'gitlab', 'github',
        'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'scikit-learn', 'keras',
        'pandas', 'numpy', 'scipy', 'matplotlib', 'seaborn', 'plotly',
        'power bi', 'tableau', 'excel', 'sheets',
        'git', 'rest api', 'graphql', 'microservices', 'agile', 'scrum',
        'linux', 'windows', 'macos', 'bash', 'shell', 'json', 'xml', 'yaml',
    ]
    
    found_skills = []
    for skill in common_skills:
        if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
            found_skills.append(skill.title())
    
    return list(set(found_skills)) if found_skills else ['Not Specified']


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = parse_resume(sys.argv[1])
        print(json.dumps(result, indent=2))
