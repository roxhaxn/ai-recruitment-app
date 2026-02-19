import re
import pdfplumber
import docx
import spacy

nlp = spacy.load("en_core_web_sm")

class ResumeParser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.text = self.extract_text()

    def extract_text(self):
        if self.file_path.endswith(".pdf"):
            text = ""
            with pdfplumber.open(self.file_path) as pdf:
                for page in pdf.pages:
                    if page.extract_text():
                        text += page.extract_text() + "\n"
            return text
        elif self.file_path.endswith(".docx"):
            doc = docx.Document(self.file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        else:
            raise ValueError("Unsupported file format")

    def extract_name(self):
        doc = nlp(self.text)
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                return ent.text
        return None

    def extract_email(self):
        match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", self.text)
        return match.group(0) if match else None

    def extract_phone(self):
        match = re.search(r"\+?\d[\d\s\-\(\)]{7,15}", self.text)
        return match.group(0) if match else None

    def extract_skills(self):
        skills = ["Python", "SQL", "Excel", "Tableau", "Power BI", "Machine Learning", "C++", "Java"]
        found = [skill for skill in skills if skill.lower() in self.text.lower()]
        return list(set(found))

    def extract_education(self):
        keywords = ["B.Tech", "B.Sc", "M.Tech", "M.Sc", "MBA", "PhD", "Bachelor", "Master"]
        found = [kw for kw in keywords if kw.lower() in self.text.lower()]
        return list(set(found))

    def get_extracted_data(self):
        return {
            "name": self.extract_name(),
            "email": self.extract_email(),
            "phone": self.extract_phone(),
            "skills": self.extract_skills(),
            "education": self.extract_education(),
        }
