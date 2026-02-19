# hr_dashboard/topsis_ranker.py
import os
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def rank_resumes(job_desc_path, parsed_resumes_folder):
    """Ranks resumes by similarity to job description"""
    if not os.path.exists(job_desc_path):
        raise FileNotFoundError(f"Job description not found: {job_desc_path}")

    with open(job_desc_path, 'r', encoding='utf-8', errors='ignore') as f:
        job_text = f.read()

    resumes = []
    for file in os.listdir(parsed_resumes_folder):
        if file.endswith('.json'):
            with open(os.path.join(parsed_resumes_folder, file), 'r', encoding='utf-8') as f:
                data = json.load(f)
                resumes.append({
                    "filename": file,
                    "text": " ".join(data.values())
                })

    if not resumes:
        return []

    # TF-IDF + cosine similarity
    docs = [job_text] + [r['text'] for r in resumes]
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf = vectorizer.fit_transform(docs)
    scores = cosine_similarity(tfidf[0:1], tfidf[1:]).flatten()

    ranked = sorted(
        zip(resumes, scores),
        key=lambda x: x[1],
        reverse=True
    )

    return [{"filename": r['filename'], "score": round(s*100, 2)} for r, s in ranked]
