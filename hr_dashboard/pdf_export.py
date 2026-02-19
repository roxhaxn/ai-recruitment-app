import re
import docx2txt
import fitz  # PyMuPDF
import os

class ResumeParser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.text = self._extract_text()

    # ---------------- Extract Raw Text ----------------
    def _extract_text(self):
        ext = os.path.splitext(self.file_path)[-1].lower()
        text = ""

        if ext == ".pdf":
            with fitz.open(self.file_path) as doc:
                for page in doc:
                    text += page.get_text("text")
        elif ext == ".docx":
            text = docx2txt.process(self.file_path)
        else:
            raise ValueError("Unsupported file format. Use PDF or DOCX.")

        return text.lower()

    # ---------------- Extract Name ----------------
    def _extract_name(self):
        # Simple heuristic: first line or first capitalized word
        lines = self.text.split("\n")
        for line in lines[:5]:  # only check top few lines
            if line.strip() and len(line.split()) <= 4:
                return line.strip().title()
        return "Unknown"

    # ---------------- Extract Email ----------------
    def _extract_email(self):
        match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", self.text)
        return match.group(0) if match else ""

    # ---------------- Extract Phone ----------------
    def _extract_phone(self):
        match = re.search(r"\+?\d[\d -]{8,12}\d", self.text)
        return match.group(0) if match else ""

    # ---------------- Extract Education ----------------
    def _extract_education(self):
        edu_keywords = {
            "phd": "PhD",
            "doctorate": "PhD",
            "master": "Masters",
            "msc": "Masters",
            "mca": "Masters",
            "mba": "Masters",
            "bachelor": "Bachelors",
            "bsc": "Bachelors",
            "btech": "Bachelors",
            "be ": "Bachelors",
            "diploma": "Diploma",
            "12th": "Diploma",
        }
        for key, val in edu_keywords.items():
            if key in self.text:
                return val
        return ""

    # ---------------- Extract Skills ----------------
    def _extract_skills(self):
        # Define a basic skillset for demo
        skills_list = [
            "python", "java", "c++", "sql", "excel", "tableau", "power bi",
            "machine learning", "deep learning", "nlp", "html", "css",
            "javascript", "react", "django", "flask", "photoshop", "figma"
        ]
        found = [skill for skill in skills_list if skill in self.text]
        return ", ".join(found) if found else ""

    # ---------------- Extract Experience ----------------
    def _extract_experience(self):
        # Look for years of experience like "3 years", "2+ years"
        match = re.search(r"(\d+)\+?\s+year", self.text)
        if match:
            return int(match.group(1))
        return 0

    # ---------------- Main Function ----------------
    def get_extracted_data(self):
        return {
            "name": self._extract_name(),
            "email": self._extract_email(),
            "phone": self._extract_phone(),
            "education": self._extract_education(),
            "skills": self._extract_skills(),
            "experience": self._extract_experience()
        }
