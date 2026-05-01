# 🎯 AI Recruitment Platform

An intelligent recruitment system that uses AI-powered resume parsing and TOPSIS ranking to match candidates with job opportunities.

## ✨ Features

- **Resume Parsing**: Automatically extract candidate info (name, email, phone, experience, education, skills)
- **Job Posting**: Recruiters can create job listings with requirements
- **Job Application**: Students can apply for jobs with cover letters
- **AI Ranking**: TOPSIS algorithm ranks candidates based on job requirements
- **Application Tracking**: Track candidate status (Applied → Interview → Accepted/Rejected)
- **Contact Management**: Direct contact with candidates via email/phone

## 🛠️ Tech Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript
- **Data Processing**: Pandas, NumPy, scikit-learn
- **PDF Parsing**: pdfplumber, pypdf
- **Storage**: JSON files

## 📋 Project Structure

```
ai recruitment app/
├── webapp/                 # Flask application
│   ├── app.py             # Main app & routes
│   ├── templates/         # HTML templates
│   └── static/            # CSS & styling
├── hr_dashboard/          # Core business logic
│   ├── resume_parser.py   # Resume parsing
│   └── topsis_ranking.py  # AI ranking algorithm
├── requirements.txt       # Dependencies
└── README.md             # This file
```

## 🚀 Installation

### 1. Clone Repository
```bash
git clone https://github.com/YOUR_USERNAME/ai-recruitment-app.git
cd ai-recruitment-app
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/Scripts/activate  # Git Bash
# or
venv\Scripts\activate  # Windows CMD
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Application
```bash
cd webapp
python app.py
```

Visit: **http://localhost:5000**

## 👥 User Roles

### Student Portal
- Upload resume (PDF)
- View available jobs
- Apply for positions
- Track application status

### Recruiter Portal
- Post job listings
- View applicants
- Rank candidates using AI
- Update application status
- Contact candidates directly

## 📊 How AI Ranking Works

The TOPSIS (Technique for Order Performance by Similarity to Ideal Solution) algorithm ranks candidates based on:

- **Experience** (20-30%)
- **Education** (10-20%)
- **Skills Match** (30-40%)
- **Semantic Fit** (25-30%)

Weights adjust automatically based on job role.

## 📁 Data Flow

```
Student uploads PDF resume
    ↓
Resume Parser extracts: name, email, phone, experience, education, skills
    ↓
Data stored in parsed_resumes/
    ↓
Recruiter posts job
    ↓
Student applies for job
    ↓
Recruiter uses AI ranking to filter & rank candidates
    ↓
Recruiter schedules interview or makes offer
```

## 🎯 Key Features Demo

### Resume Parsing
- Extracts candidate information automatically
- Supports any resume format (PDF)
- Parses: contact info, experience, education, skills

### Smart Ranking
- Role-based weight presets
- Constraint filtering (seniority, education)
- Semantic job description matching

### Application Tracking
- Real-time status updates
- Direct candidate contact
- Interview scheduling

## 📞 Contact Information

After uploading resume, students provide:
- Email address
- Phone number
- Target role
- Education level
- Work mode preference

Recruiters can directly contact candidates from the applicant portal.

## 🔒 Data Storage

All data stored in JSON files:
- `webapp/data/jobs.json` - Job listings
- `webapp/data/applications.json` - Job applications
- `webapp/data/students.json` - Student profiles
- `hr_dashboard/parsed_resumes/` - Parsed resume data

## 🎓 Interview Ready

This project demonstrates:
✅ Full-stack web development (Flask + HTML/CSS/JS)
✅ PDF processing & data extraction
✅ Machine learning (TOPSIS ranking algorithm)
✅ Database design (JSON file storage)
✅ User authentication & multi-role system
✅ Real-time application tracking
✅ REST API design patterns

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Feel free to fork, modify, and submit pull requests!

---

**Built with ❤️ for smart recruitment**