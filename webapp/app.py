# webapp/app.py
import os, sys, json, uuid
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

# Ensure project root is importable so hr_dashboard.* works
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import your existing backend functions
# resume_parser.parse_resume(path) -> dict
# topsis_ranking.topsis(df, weights) -> ranked_df
from hr_dashboard.resume_parser import parse_resume
from hr_dashboard.topsis_ranking import topsis

# For DataFrame handling before calling topsis
import pandas as pd

# App setup
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "hire_smart_dev_key")

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
HR_DASH = PROJECT_ROOT / "hr_dashboard"
PARSED_DIR = HR_DASH / "parsed_resumes"
UPLOADS_DIR = HR_DASH / "uploads"
WEB_DATA_DIR = Path(__file__).resolve().parent / "data"
JOBS_FILE = WEB_DATA_DIR / "jobs.json"
APPLICATIONS_FILE = WEB_DATA_DIR / "applications.json"

# Ensure directories exist
PARSED_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
WEB_DATA_DIR.mkdir(parents=True, exist_ok=True)
for f in (JOBS_FILE, APPLICATIONS_FILE):
    if not f.exists():
        f.write_text("[]", encoding="utf-8")

# Predefined roles (Slickit parity) and default TOPSIS weights (tweakable)
ROLE_WEIGHTS = {
    "Data Analyst": {"experience": 0.35, "education": 0.25, "skills": 0.40},
    "Data Scientist": {"experience": 0.30, "education": 0.30, "skills": 0.40},
    "Machine Learning Engineer": {"experience": 0.30, "education": 0.25, "skills": 0.45},
    "Software Developer": {"experience": 0.40, "education": 0.20, "skills": 0.40},
    "Web Developer": {"experience": 0.35, "education": 0.20, "skills": 0.45}
}

# ----------------------
# Helpers
# ----------------------
def load_json(file_path):
    if Path(file_path).exists():
        return json.loads(Path(file_path).read_text(encoding="utf-8"))
    return []

def save_json(file_path, obj):
    Path(file_path).write_text(json.dumps(obj, indent=2), encoding="utf-8")

def list_parsed_resumes():
    """Return list of parsed resume dicts from hr_dashboard/parsed_resumes."""
    out = []
    for p in sorted(PARSED_DIR.glob("*.json")):
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            continue
    return out

def save_uploaded_pdf(uploaded_file):
    """Save uploaded file to hr_dashboard/uploads and return saved path."""
    filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}_{secure_filename(uploaded_file.filename)}"
    path = UPLOADS_DIR / filename
    uploaded_file.save(str(path))
    return path

# werkzeug secure_filename shim (avoid import errors)
def secure_filename(name: str) -> str:
    # very small sanitization
    return "".join(c for c in name if c.isalnum() or c in (" ", ".", "_", "-")).rstrip()

def normalized_dataframe_from_parsed(parsed_list):
    """
    Convert parser output list-of-dicts into DataFrame expected by topsis:
    required columns: name, experience, education, skills
    This function handles missing keys with sensible defaults.
    """
    rows = []
    for d in parsed_list:
        # name
        name = d.get("name") or d.get("full_name") or d.get("candidate_name") or d.get("filename") or "Unknown"

        # experience: try many fields, extract first integer found
        exp = 0
        for key in ("experience", "experience_years", "total_experience", "years"):
            if key in d and d[key]:
                try:
                    s = str(d[key])
                    nums = [int(t) for t in "".join(ch if ch.isdigit() else " " for ch in s).split() if t.isdigit()]
                    if nums:
                        exp = nums[0]
                        break
                except Exception:
                    continue

        # education: try degrees list or education string
        edu = ""
        if "education" in d:
            if isinstance(d["education"], list) and d["education"]:
                edu = d["education"][0]
            elif isinstance(d["education"], str):
                edu = d["education"]
        elif "degrees" in d:
            deg = d.get("degrees")
            if isinstance(deg, list) and deg:
                edu = deg[0]
            elif isinstance(deg, str):
                edu = deg

        # skills: list or comma string -> convert to comma string
        skills = ""
        if "skills" in d:
            if isinstance(d["skills"], list):
                skills = ", ".join([str(s).strip() for s in d["skills"] if s])
            else:
                skills = str(d["skills"])
        elif "key_skills" in d:
            skills = str(d["key_skills"])

        rows.append({
            "name": name,
            "experience": exp,
            "education": edu,
            "skills": skills
        })
    # Build DataFrame
    df = pd.DataFrame(rows)
    # ensure columns exist
    for c in ["name", "experience", "education", "skills"]:
        if c not in df.columns:
            df[c] = 0 if c == "experience" else ""
    return df

# ----------------------
# ROUTES
# ----------------------
@app.route("/")
def index():
    return render_template("index.html")

# STUDENT: upload resume and view available jobs
@app.route("/student", methods=["GET", "POST"])
def student():
    jobs = load_json(JOBS_FILE)
    applications = load_json(APPLICATIONS_FILE)

    if request.method == "POST":
        # file input name: 'resume'
        file = request.files.get("resume")
        student_name = request.form.get("name", "").strip()

        if not file or file.filename == "":
            flash("Please choose a PDF resume to upload.", "danger")
            return redirect(url_for("student"))

        if not file.filename.lower().endswith(".pdf"):
            flash("Currently only PDF resumes are supported. Please upload a PDF.", "warning")
            return redirect(url_for("student"))

        # Save uploaded PDF
        saved_pdf = UPLOADS_DIR / secure_filename(file.filename)
        file.save(str(saved_pdf))

        # Parse the resume using your parser (expects path)
        try:
            parsed = parse_resume(str(saved_pdf))
        except Exception as e:
            flash(f"Resume parser error: {e}", "danger")
            return redirect(url_for("student"))

        # Save parsed JSON into parsed_resumes with unique name
        out_name = f"{student_name.replace(' ', '_')}_{uuid.uuid4().hex[:8]}.json" if student_name else f"anon_{uuid.uuid4().hex[:8]}.json"
        out_path = PARSED_DIR / out_name
        out_path.write_text(json.dumps(parsed, indent=2), encoding="utf-8")

        # Optionally record application entry if student applied to job while uploading (not required)
        flash("Resume uploaded and parsed successfully — recruiters can now see your profile.", "success")
        return redirect(url_for("student"))

    # GET
    return render_template("student.html", jobs=jobs, applications=applications)

# Student applies to a job (simple local tracking)
@app.route("/apply", methods=["POST"])
def apply():
    student_name = request.form.get("student_name", "Anonymous")
    job_id = request.form.get("job_id")
    jobs = load_json(JOBS_FILE)
    job = next((j for j in jobs if j["id"] == job_id), None)
    if not job:
        flash("Job not found.", "danger")
        return redirect(url_for("student"))

    applications = load_json(APPLICATIONS_FILE)
    applications.append({
        "id": str(uuid.uuid4()),
        "job_id": job_id,
        "student_name": student_name,
        "applied_at": datetime.utcnow().isoformat()
    })
    save_json(APPLICATIONS_FILE, applications)
    flash(f"Applied to {job['role']} @ {job['company']}", "success")
    return redirect(url_for("student"))

# RECRUITER: post job or run ranking
@app.route("/recruiter", methods=["GET", "POST"])
def recruiter():
    if request.method == "POST":
        # --- Get inputs from the recruiter form ---
        role = request.form.get("role")
        job_description = request.form.get("description")

        # --- Collect weights from the form ---
        weights = {
            "experience": float(request.form.get("experience", 0.25)),
            "education": float(request.form.get("education", 0.15)),
            "skills": float(request.form.get("skills", 0.25)),
            "semantic_fit": float(request.form.get("semantic_fit", 0.35))
        }

        # --- Load all parsed resumes from folder ---
        
        
        resumes = []
        for file in os.listdir(PARSED_DIR):
            if file.endswith(".json"):
                with open(os.path.join(PARSED_DIR, file), "r", encoding="utf-8") as f:
                    resumes.append(json.load(f))

        # --- Check if any resumes exist ---
        if not resumes:
            flash("⚠️ No resumes found. Ask students to upload first!", "danger")
            return redirect(url_for("recruiter"))

        # --- Convert to DataFrame for TOPSIS ---
        df = pd.DataFrame(resumes)

        # --- Run the hybrid Semantic + TOPSIS ranking ---
        ranked = topsis(df, weights, job_description)
        ranked_records = ranked.to_dict(orient="records")

        # --- Display results page ---
        return render_template("results.html", ranked=ranked_records, role=role)

    # --- For GET request: just render the recruiter form ---
    return render_template("recruiter.html")


# Results (simple route to render results if needed)
@app.route("/results")
def results():
    # Not used directly; results are rendered from recruiter route after ranking
    return redirect(url_for("recruiter"))

# Debug endpoints (optional)
@app.route("/_debug/list_parsed")
def _debug_list_parsed():
    parsed = list_parsed_resumes()
    return jsonify({"count": len(parsed), "samples": parsed[:5]})

@app.route("/_debug/jobs")
def _debug_jobs():
    return jsonify(load_json(JOBS_FILE))

# ------------------------------
# POST JOB LISTING (STEP 4.1)
# ------------------------------
@app.route("/post_job", methods=["POST"])
def post_job():
    # Read form inputs
    company = request.form.get("company")
    role = request.form.get("role")
    positions = request.form.get("positions")
    description = request.form.get("description")

    # Validate
    if not company or not role or not positions:
        flash("⚠️ Please fill all required fields.", "danger")
        return redirect(url_for("recruiter"))

    # Build job entry
    new_job = {
        "company": company,
        "role": role,
        "positions": int(positions),
        "description": description
    }

    # Load existing jobs
    jobs_file = os.path.join(os.path.dirname(__file__), "data", "jobs.json")
    if os.path.exists(jobs_file):
        with open(jobs_file, "r", encoding="utf-8") as f:
            jobs = json.load(f)
    else:
        jobs = []

    # Add new job
    jobs.append(new_job)

    # Save updated list
    with open(jobs_file, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=4)

    flash("✅ Job posted successfully!", "success")
    return redirect(url_for("recruiter"))



# ----------------------
# Run
# ----------------------
if __name__ == "__main__":
    app.run(debug=True)
