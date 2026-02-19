import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer, util

# Load lightweight embedding model once
model = SentenceTransformer('all-MiniLM-L6-v2')

def compute_semantic_similarity(job_description, resumes_text):
    """Compute cosine similarity between job description and resumes."""
    job_emb = model.encode(job_description, convert_to_tensor=True)
    resume_embs = model.encode(resumes_text, convert_to_tensor=True)
    sims = util.cos_sim(job_emb, resume_embs)[0].cpu().numpy()
    return sims  # list of similarity scores

def topsis(df, weights, job_description=None):
    """Apply TOPSIS ranking with optional semantic similarity."""
    edu_map = {"phd": 4, "masters": 3, "bachelors": 2, "diploma": 1, "": 0}

    df_numeric = pd.DataFrame()
    df_numeric["name"] = df["name"]
    df_numeric["experience"] = df["experience"].apply(lambda x: int(x) if str(x).isdigit() else 0)
    df_numeric["education"] = df["education"].apply(lambda x: edu_map.get(str(x).lower(), 0))
    df_numeric["skills"] = df["skills"].apply(lambda x: len(str(x).split(",")) if isinstance(x, str) else 0)

    criteria = ["experience", "education", "skills"]

    # Add semantic fit
    if job_description:
        df_numeric["semantic_fit"] = compute_semantic_similarity(job_description, df["text"].tolist())
        criteria.append("semantic_fit")

    # Normalize
    matrix = df_numeric[criteria].to_numpy(dtype=float)
    norm = np.linalg.norm(matrix, axis=0)
    norm_matrix = matrix / norm

    # Apply weights
    weight_vector = np.array([weights[c] for c in criteria])
    weighted_matrix = norm_matrix * weight_vector

    # Ideal best/worst
    ideal_best = np.max(weighted_matrix, axis=0)
    ideal_worst = np.min(weighted_matrix, axis=0)

    # Distances
    dist_best = np.linalg.norm(weighted_matrix - ideal_best, axis=1)
    dist_worst = np.linalg.norm(weighted_matrix - ideal_worst, axis=1)

    # Score
    score = dist_worst / (dist_best + dist_worst)
    df_numeric["score"] = score

    ranked_df = df_numeric.sort_values(by="score", ascending=False).reset_index(drop=True)
    return ranked_df
