# hr_dashboard/scoring.py
import pandas as pd
import numpy as np

# Education level mapping
education_map = {
    "B.Tech": 3,
    "B.Sc": 2,
    "M.Sc": 4,
    "MBA": 4,
    "BBA": 2
}

def normalize_series(series):
    """Normalize a pandas series to 0-1"""
    if series.max() == series.min():
        return series / series.max() if series.max() != 0 else series
    return (series - series.min()) / (series.max() - series.min())

def compute_skill_score(candidate_skills, job_skills):
    """Compute role-specific skill match percentage"""
    if not job_skills:
        return 0
    match_count = len(set(candidate_skills).intersection(set(job_skills)))
    return match_count / len(job_skills)

def topsis_ranking(candidate_df, job_skills, required_exp, required_edu, weights):
    """
    Returns candidate_df with normalized scores, TOPSIS score, and Rank
    """
    df = candidate_df.copy()
    
    # Experience Score: candidate years / required years (max 1)
    df['Experience_Score'] = df['experience'].apply(lambda x: min(float(x)/required_exp,1) if required_exp>0 else 1)
    
    # Education Score: map degree to numeric / max
    df['Education_Score'] = df['education'].apply(lambda x: education_map.get(x,2)/max(education_map.values()))
    
    # Skills Score: role-specific match %
    df['Skills_Score'] = df['skills'].apply(lambda x: compute_skill_score(x, job_skills))
    
    # Normalize all scores (0-1)
    for col in ['Experience_Score','Education_Score','Skills_Score']:
        df[col] = normalize_series(df[col])
    
    # Apply TOPSIS
    # Step 1: multiply by weights
    df['Weighted_Exp'] = df['Experience_Score'] * weights['experience']
    df['Weighted_Edu'] = df['Education_Score'] * weights['education']
    
    skill_weights = weights.get('skills', {})
    df['Weighted_Skills'] = df['Skills_Score'] * sum(skill_weights.values())  # simple aggregate
    
    df['Topsis_Score'] = df['Weighted_Exp'] + df['Weighted_Edu'] + df['Weighted_Skills']
    
    # Rank candidates (higher TOPSIS score = better)
    df['Rank'] = df['Topsis_Score'].rank(ascending=False, method='min').astype(int)
    
    return df.sort_values(by='Rank')
