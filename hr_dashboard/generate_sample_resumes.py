from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

# Folder where the resumes will be stored
output_folder = "resumes"
os.makedirs(output_folder, exist_ok=True)

def create_resume(filename, name, email, phone, skills, experience, education, projects):
    filepath = os.path.join(output_folder, filename)
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 18)
    c.drawString(100, height - 100, name)

    c.setFont("Helvetica", 12)
    c.drawString(100, height - 130, f"Email: {email}")
    c.drawString(100, height - 150, f"Phone: {phone}")

    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, height - 180, "Skills:")
    c.setFont("Helvetica", 12)
    c.drawString(120, height - 200, ", ".join(skills))

    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, height - 230, "Experience:")
    c.setFont("Helvetica", 12)
    c.drawString(120, height - 250, experience)

    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, height - 280, "Education:")
    c.setFont("Helvetica", 12)
    c.drawString(120, height - 300, education)

    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, height - 330, "Projects:")
    c.setFont("Helvetica", 12)
    c.drawString(120, height - 350, projects)

    c.save()
    print(f"✅ Created: {filename}")

# Sample resumes
resumes = [
    ("resume_rohan.pdf", "Rohan Yadav", "rohan@example.com", "9876543210",
     ["Python", "SQL", "Tableau", "Data Analysis"],
     "2 years as Data Analyst at Infosys",
     "B.Tech in Computer Science, Delhi University",
     "Customer Churn Prediction, Sales Dashboard using Power BI"),

    ("resume_priya.pdf", "Priya Sharma", "priya@example.com", "9876501234",
     ["Java", "Spring Boot", "MySQL", "Docker"],
     "3 years as Backend Developer at TCS",
     "B.E. in Information Technology, Mumbai University",
     "E-commerce API system, Inventory Management App"),

    ("resume_rahul.pdf", "Rahul Mehta", "rahul@example.com", "9988776655",
     ["Machine Learning", "Python", "TensorFlow", "NLP"],
     "1.5 years as ML Engineer at Wipro",
     "M.Tech in AI, IIT Kanpur",
     "Sentiment Analysis model, Resume Screening Tool"),
]

for args in resumes:
    create_resume(*args)

print("\n🎯 All sample resumes created in /resumes folder!")

