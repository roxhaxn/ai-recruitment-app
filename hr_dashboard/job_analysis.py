# hr_dashboard/job_analysis.py
import re

def analyze_job_description(job_desc, possible_skills):
    # Extract skills
    job_skills = [skill for skill in possible_skills if re.search(skill, job_desc, re.I)]
    
    # Extract experience
    exp_match = re.findall(r'(\d+)\+?\s+years', job_desc)
    required_experience = max([int(x) for x in exp_match], default=0)
    
    # Extract education
    education_levels = ["B.Tech","B.Sc","M.Sc","MBA","BBA"]
    job_education = [edu for edu in education_levels if re.search(edu, job_desc, re.I)]
    
    # Generate dynamic weights
    weights = {
        "experience": 0.3,
        "education": 0.15,
        "skills": {skill: 0.55/len(job_skills) for skill in job_skills} if job_skills else {}
    }
    
    return job_skills, required_experience, job_education, weights
