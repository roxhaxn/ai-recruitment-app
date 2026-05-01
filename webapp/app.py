# webapp/app.py
import os
import sys
import json
import uuid
from datetime import datetime
from pathlib import Path

import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from hr_dashboard.resume_parser import parse_resume
from hr_dashboard.topsis_ranking import topsis

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "hire_smart_dev_key")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
HR_DASH = PROJECT_ROOT / "hr_dashboard"
PARSED_DIR = HR_DASH / "parsed_resumes"
UPLOADS_DIR = HR_DASH / "uploads"

WEB_DATA_DIR = Path(__file__).resolve().parent / "data"
JOBS_FILE = WEB_DATA_DIR / "jobs.json"
APPLICATIONS_FILE = WEB_DATA_DIR / "applications.json"
STUDENTS_FILE = WEB_DATA_DIR / "students.json"

ALLOWED_EXTENSIONS = {"pdf"}

ROLE_WEIGHT_PRESETS = {
    "Data Analyst": {"experience": 0.20, "education": 0.15, "skills": 0.35, "semantic_fit": 0.30},
    "Data Scientist": {"experience": 0.25, "education": 0.20, "skills": 0.30, "semantic_fit": 0.25},
    "Machine Learning Engineer": {"experience": 0.25, "education": 0.15, "skills": 0.35, "semantic_fit": 0.25},
    "Software Developer": {"experience": 0.30, "education": 0.10, "skills": 0.35, "semantic_fit": 0.25},
    "Web Developer": {"experience": 0.25, "education": 0.10, "skills": 0.40, "semantic_fit": 0.25},
}

ROLE_OPTIONS = list(ROLE_WEIGHT_PRESETS.keys())

SENIORITY_OPTIONS = ["Any", "Intern", "Fresher", "Junior", "Mid", "Senior", "Lead"]
EDUCATION_OPTIONS = ["Any", "Diploma", "Bachelors", "Masters", "PhD"]
WORK_MODE_OPTIONS = ["Any", "On-site", "Hybrid", "Remote"]
EMPLOYMENT_TYPE_OPTIONS = ["Any", "Full-time", "Part-time", "Contract", "Internship"]
SKILL_OPTIONS = [
    "Python", "SQL", "Excel", "Pandas", "NumPy", "Machine Learning", "Deep Learning",
    "Power BI", "Tableau", "Java", "JavaScript", "React", "Node.js", "Flask", "Django",
    "AWS", "Docker",
]

EDU_SCORE = {"": 0, "Diploma": 1, "Bachelors": 2, "Masters": 3, "PhD": 4}
SENIORITY_MIN_EXP = {"Any": 0, "Intern": 0, "Fresher": 0, "Junior": 1, "Mid": 3, "Senior": 5, "Lead": 7}

PARSED_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
WEB_DATA_DIR.mkdir(parents=True, exist_ok=True)

for f in (JOBS_FILE, APPLICATIONS_FILE, STUDENTS_FILE):
    if not f.exists():
        f.write_text("[]", encoding="utf-8")


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def load_json(file_path):
    try:
        p = Path(file_path)
        if p.exists():
            text = p.read_text(encoding="utf-8").strip()
            return json.loads(text) if text else []
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
    return []


def save_json(file_path, obj):
    try:
        Path(file_path).write_text(json.dumps(obj, indent=2, default=str), encoding="utf-8")
    except Exception as e:
        print(f"Error saving {file_path}: {e}")


def safe_name(name: str) -> str:
    return secure_filename(name or "file")


def list_parsed_resumes():
    out = []
    for p in sorted(PARSED_DIR.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                if isinstance(data.get("resume"), dict):
                    record = dict(data["resume"])
                    record["student_meta"] = data.get("meta", {})
                else:
                    record = data
                record["_filename"] = p.name
                out.append(record)
        except Exception as e:
            print(f"Error loading resume {p.name}: {e}")
    return out


def normalize_experience(value):
    if value is None:
        return 0
    s = str(value)
    digits = "".join(ch if ch.isdigit() else " " for ch in s).split()
    return int(digits[0]) if digits else 0


def normalize_education(value):
    if isinstance(value, list) and value:
        value = value[0]
    s = str(value or "").lower()
    if "phd" in s or "doctor" in s:
        return "PhD"
    if "master" in s or "mba" in s or "m.tech" in s or "msc" in s:
        return "Masters"
    if "bachelor" in s or "b.tech" in s or "bsc" in s or "ba" in s:
        return "Bachelors"
    if "diploma" in s:
        return "Diploma"
    return ""


def normalize_skills(value):
    if isinstance(value, list):
        return ", ".join(str(x).strip() for x in value if x)
    return str(value or "")


def normalized_dataframe_from_parsed(parsed_list):
    rows = []
    for d in parsed_list:
        name = (
            d.get("name")
            or d.get("full_name")
            or d.get("candidate_name")
            or d.get("student_name")
            or d.get("_filename", "Unknown").replace(".json", "")
        )
        exp = normalize_experience(
            d.get("experience")
            or d.get("experience_years")
            or d.get("total_experience")
            or d.get("years")
        )
        edu = normalize_education(d.get("education") or d.get("degrees"))
        skills = normalize_skills(d.get("skills") or d.get("key_skills"))

        rows.append({
            "name": name,
            "experience": exp,
            "education": edu,
            "skills": skills,
        })

    if not rows:
        return pd.DataFrame(columns=["name", "experience", "education", "skills"])
    
    df = pd.DataFrame(rows)
    for col in ["name", "experience", "education", "skills"]:
        if col not in df.columns:
            df[col] = 0 if col == "experience" else ""
    return df[["name", "experience", "education", "skills"]]


def get_weights_for_role(role: str):
    return ROLE_WEIGHT_PRESETS.get(role, {"experience": 0.25, "education": 0.15, "skills": 0.35, "semantic_fit": 0.25})


def build_job_description(role, seniority, education_level, work_mode, employment_type, skill_focus, extra_text):
    parts = [role, seniority, education_level, work_mode, employment_type]
    if skill_focus:
        parts.extend(skill_focus)
    if extra_text:
        parts.append(extra_text)
    return " | ".join([p for p in parts if p and p != "Any"])


def apply_constraints(df, seniority, education_level):
    result = df.copy()

    min_exp = SENIORITY_MIN_EXP.get(seniority or "Any", 0)
    if min_exp > 0 and "experience" in result.columns:
        result = result[result["experience"].fillna(0) >= min_exp]

    edu_required = education_level or "Any"
    if edu_required != "Any" and "education" in result.columns:
        req_score = EDU_SCORE.get(edu_required, 0)
        def edu_score(v):
            return EDU_SCORE.get(normalize_education(v), 0)
        result = result[result["education"].apply(edu_score) >= req_score]

    return result


def get_student_by_name(name):
    """Get student info by name from students.json"""
    students = load_json(STUDENTS_FILE)
    for student in students:
        if student.get("name").lower() == name.lower():
            return student
    return None


def get_applications_by_job(job_id):
    """Get all applications for a specific job"""
    applications = load_json(APPLICATIONS_FILE)
    job_apps = [app for app in applications if app.get("job_id") == job_id]
    
    # Enrich with student details
    for app in job_apps:
        student = get_student_by_name(app.get("student_name"))
        if student:
            app["email"] = student.get("email", "N/A")
            app["phone"] = student.get("phone", "N/A")
            app["resume_path"] = student.get("resume_path", "")
    
    return job_apps


@app.route("/", endpoint="index")
def index():
    return render_template("index.html")


@app.route("/student", endpoint="student", methods=["GET", "POST"])
@app.route("/students", endpoint="students", methods=["GET", "POST"])
def students():
    jobs = load_json(JOBS_FILE)
    applications = load_json(APPLICATIONS_FILE)
    students_list = load_json(STUDENTS_FILE)

    if request.method == "POST":
        file = request.files.get("resume")
        student_name = request.form.get("name", "").strip()
        student_email = request.form.get("email", "").strip()
        student_phone = request.form.get("phone", "").strip()
        target_role = request.form.get("target_role", "Any")
        highest_education = request.form.get("highest_education", "Any")
        preferred_work_mode = request.form.get("preferred_work_mode", "Any")

        # Validation
        if not student_name:
            flash("Please enter your name.", "danger")
            return redirect(url_for("students"))

        if not student_email:
            flash("Please enter your email.", "danger")
            return redirect(url_for("students"))

        if not file or file.filename == "":
            flash("Please choose a PDF resume.", "danger")
            return redirect(url_for("students"))

        if not allowed_file(file.filename):
            flash("Only PDF files are supported.", "danger")
            return redirect(url_for("students"))

        # Save PDF
        filename = safe_name(file.filename)
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        unique_id = uuid.uuid4().hex[:8]
        saved_pdf = UPLOADS_DIR / f"{timestamp}_{unique_id}_{filename}"
        
        try:
            file.save(str(saved_pdf))
        except Exception as e:
            flash(f"Error saving file: {str(e)}", "danger")
            return redirect(url_for("students"))

        # Parse resume
        try:
            parsed = parse_resume(str(saved_pdf))
            if "error" in parsed:
                flash(f"Parse error: {parsed['error']}", "danger")
                return redirect(url_for("students"))
        except Exception as e:
            flash(f"Resume parsing failed: {str(e)}", "danger")
            return redirect(url_for("students"))

        # Store student info
        student_record = {
            "id": unique_id,
            "name": student_name,
            "email": student_email,
            "phone": student_phone,
            "target_role": target_role,
            "highest_education": highest_education,
            "preferred_work_mode": preferred_work_mode,
            "resume_path": str(saved_pdf.name),
            "uploaded_at": datetime.utcnow().isoformat(),
        }

        students_list.append(student_record)
        save_json(STUDENTS_FILE, students_list)

        # Store parsed data with metadata
        payload = {
            "meta": {
                "student_name": student_name,
                "student_email": student_email,
                "student_phone": student_phone,
                "target_role": target_role,
                "highest_education": highest_education,
                "preferred_work_mode": preferred_work_mode,
                "uploaded_at": datetime.utcnow().isoformat(),
                "source_pdf": saved_pdf.name,
            },
            "resume": parsed,
        }

        out_name = safe_name(f"{student_name}_{unique_id}.json")
        out_path = PARSED_DIR / out_name
        
        try:
            out_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        except Exception as e:
            flash(f"Error storing resume: {str(e)}", "danger")
            return redirect(url_for("students"))

        flash(f"✅ Resume uploaded and parsed successfully, {student_name}!", "success")
        return redirect(url_for("students"))

    # Get student's applications
    student_name = request.args.get("student_name", "")
    my_applications = [app for app in applications if app.get("student_name") == student_name] if student_name else []

    return render_template(
        "students.html",
        jobs=jobs,
        applications=applications,
        my_applications=my_applications,
        student_name=student_name,
        role_options=["Any"] + ROLE_OPTIONS,
        education_options=EDUCATION_OPTIONS,
        work_mode_options=WORK_MODE_OPTIONS,
    )


@app.route("/apply_job", methods=["POST"])
def apply_job():
    """Student applies for a job"""
    student_name = request.form.get("student_name", "").strip()
    job_id = request.form.get("job_id", "").strip()
    message = request.form.get("message", "").strip()

    if not student_name or not job_id:
        flash("Invalid application data.", "danger")
        return redirect(url_for("students"))

    # Check if student exists
    student = get_student_by_name(student_name)
    if not student:
        flash("Please upload your resume first.", "danger")
        return redirect(url_for("students"))

    # Check if job exists
    jobs = load_json(JOBS_FILE)
    job = next((j for j in jobs if str(j.get("id")) == str(job_id)), None)
    if not job:
        flash("Job not found.", "danger")
        return redirect(url_for("students"))

    # Check if already applied
    applications = load_json(APPLICATIONS_FILE)
    already_applied = any(
        app.get("student_name") == student_name and app.get("job_id") == job_id
        for app in applications
    )
    
    if already_applied:
        flash("You have already applied for this job.", "warning")
        return redirect(url_for("students") + f"?student_name={student_name}")

    # Create application
    application = {
        "id": str(uuid.uuid4()),
        "job_id": job_id,
        "student_id": student.get("id"),
        "student_name": student_name,
        "email": student.get("email"),
        "phone": student.get("phone"),
        "message": message,
        "status": "Applied",
        "applied_at": datetime.utcnow().isoformat(),
    }

    applications.append(application)
    save_json(APPLICATIONS_FILE, applications)

    flash(f"✅ Applied to {job['role']} @ {job['company']}!", "success")
    return redirect(url_for("students") + f"?student_name={student_name}")


@app.route("/recruiter", endpoint="recruiter", methods=["GET", "POST"])
@app.route("/recruiters", endpoint="recruiters", methods=["GET", "POST"])
def recruiters():
    jobs = load_json(JOBS_FILE)

    if request.method == "POST":
        role = request.form.get("role", "").strip()
        seniority = request.form.get("seniority", "Any")
        education_level = request.form.get("education_level", "Any")
        work_mode = request.form.get("work_mode", "Any")
        employment_type = request.form.get("employment_type", "Any")
        required_skills = request.form.getlist("required_skills")
        extra_text = request.form.get("description", "").strip()

        if not role:
            flash("Please select a role.", "danger")
            return redirect(url_for("recruiters"))

        parsed_resumes = list_parsed_resumes()
        if not parsed_resumes:
            flash("⚠️ No resumes uploaded yet. Please ask students to upload first.", "warning")
            return redirect(url_for("recruiters"))

        df = normalized_dataframe_from_parsed(parsed_resumes)
        
        if df.empty:
            flash("⚠️ Could not process resumes.", "danger")
            return redirect(url_for("recruiters"))

        df = apply_constraints(df, seniority, education_level)

        if df.empty:
            flash("No candidates match the selected constraints.", "warning")
            return redirect(url_for("recruiters"))

        weights = get_weights_for_role(role)
        job_description = build_job_description(role, seniority, education_level, work_mode, employment_type, required_skills, extra_text)

        try:
            ranked = topsis(df, weights, job_description)
        except Exception as e:
            flash(f"Ranking error: {str(e)}", "danger")
            return redirect(url_for("recruiters"))

        return render_template(
            "results.html",
            ranked=ranked.to_dict(orient="records"),
            role=role,
            job_description=job_description,
            weights=weights,
        )

    return render_template(
        "recruiters.html",
        role_options=ROLE_OPTIONS,
        seniority_options=SENIORITY_OPTIONS,
        education_options=EDUCATION_OPTIONS,
        work_mode_options=WORK_MODE_OPTIONS,
        employment_type_options=EMPLOYMENT_TYPE_OPTIONS,
        skill_options=SKILL_OPTIONS,
        jobs=jobs,
    )


@app.route("/post_job", methods=["POST"])
def post_job():
    company = request.form.get("company", "").strip()
    role = request.form.get("role", "").strip()
    positions = request.form.get("positions", "").strip()
    seniority = request.form.get("seniority", "Any")
    education_level = request.form.get("education_level", "Any")
    work_mode = request.form.get("work_mode", "Any")
    employment_type = request.form.get("employment_type", "Any")
    required_skills = request.form.getlist("required_skills")
    description = request.form.get("description", "").strip()

    if not company or not role or not positions:
        flash("Please fill all required fields.", "danger")
        return redirect(url_for("recruiters"))

    try:
        positions = int(positions)
    except ValueError:
        flash("Positions must be a number.", "danger")
        return redirect(url_for("recruiters"))

    jobs = load_json(JOBS_FILE)
    jobs.append({
        "id": str(uuid.uuid4()),
        "company": company,
        "role": role,
        "positions": positions,
        "seniority": seniority,
        "education_level": education_level,
        "work_mode": work_mode,
        "employment_type": employment_type,
        "required_skills": required_skills,
        "description": description,
        "posted_at": datetime.utcnow().isoformat(),
    })
    save_json(JOBS_FILE, jobs)
    flash(f"✅ Job '{role}' posted successfully at {company}!", "success")
    return redirect(url_for("recruiters"))


@app.route("/job/<job_id>/applicants", endpoint="job_applicants")
def job_applicants(job_id):
    """View all applicants for a job"""
    jobs = load_json(JOBS_FILE)
    job = next((j for j in jobs if str(j.get("id")) == str(job_id)), None)
    
    if not job:
        flash("Job not found.", "danger")
        return redirect(url_for("recruiters"))

    applicants = get_applications_by_job(job_id)

    return render_template(
        "applicants.html",
        job=job,
        applicants=applicants,
    )


@app.route("/update_application_status", methods=["POST"])
def update_application_status():
    """Update application status (Accept/Reject/Interview)"""
    app_id = request.form.get("app_id", "").strip()
    status = request.form.get("status", "").strip()

    if not app_id or status not in ["Applied", "Interview", "Accepted", "Rejected"]:
        flash("Invalid status update.", "danger")
        return redirect(url_for("recruiters"))

    applications = load_json(APPLICATIONS_FILE)
    for app in applications:
        if app.get("id") == app_id:
            app["status"] = status
            app["updated_at"] = datetime.utcnow().isoformat()
            save_json(APPLICATIONS_FILE, applications)
            flash(f"✅ Application status updated to {status}.", "success")
            return redirect(request.referrer or url_for("recruiters"))

    flash("Application not found.", "danger")
    return redirect(url_for("recruiters"))


@app.route("/results", endpoint="results")
def results():
    return redirect(url_for("recruiters"))


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
