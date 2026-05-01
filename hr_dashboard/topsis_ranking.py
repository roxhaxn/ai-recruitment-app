import re
import pandas as pd


def _num(val):
    if val is None:
        return 0
    m = re.search(r"\d+", str(val))
    return int(m.group()) if m else 0


def _education_score(val):
    s = str(val or "").lower()
    if "phd" in s or "doctor" in s:
        return 4
    if "master" in s or "mba" in s or "msc" in s or "m.tech" in s:
        return 3
    if "bachelor" in s or "b.tech" in s or "bsc" in s or "ba" in s:
        return 2
    if "diploma" in s:
        return 1
    return 0


def _skills_score(val):
    if isinstance(val, list):
        return len([x for x in val if str(x).strip()])
    s = str(val or "")
    if not s.strip():
        return 0
    return len([x for x in s.split(",") if x.strip()])


def _semantic_fit(text, job_description):
    if not job_description:
        return 0.0
    a = set(re.findall(r"[a-zA-Z]+", str(text or "").lower()))
    b = set(re.findall(r"[a-zA-Z]+", str(job_description or "").lower()))
    if not a or not b:
        return 0.0
    return len(a & b) / max(1, len(b))


def _minmax(series):
    if series.max() == series.min():
        return series * 0
    return (series - series.min()) / (series.max() - series.min())


def topsis(df, weights=None, job_description=""):
    df = df.copy()

    for col in ["name", "experience", "education", "skills"]:
        if col not in df.columns:
            df[col] = "" if col != "experience" else 0

    df["experience"] = df["experience"].apply(_num)
    df["education_score"] = df["education"].apply(_education_score)
    df["skills_score"] = df["skills"].apply(_skills_score)
    df["semantic_fit"] = df.apply(
        lambda r: _semantic_fit(f"{r['name']} {r['education']} {r['skills']} {r['experience']}", job_description),
        axis=1,
    )

    weights = weights or {}
    w_exp = float(weights.get("experience", 0.35))
    w_edu = float(weights.get("education", 0.25))
    w_skills = float(weights.get("skills", 0.40))
    w_sem = float(weights.get("semantic_fit", 0.0))

    total = w_exp + w_edu + w_skills + w_sem
    if total <= 0:
        w_exp, w_edu, w_skills, w_sem = 0.35, 0.25, 0.40, 0.0
        total = 1.0

    w_exp /= total
    w_edu /= total
    w_skills /= total
    w_sem /= total

    df["score"] = (
        _minmax(df["experience"]) * w_exp
        + _minmax(df["education_score"]) * w_edu
        + _minmax(df["skills_score"]) * w_skills
        + _minmax(df["semantic_fit"]) * w_sem
    )

    df = df.sort_values("score", ascending=False).reset_index(drop=True)
    df["rank"] = range(1, len(df) + 1)
    return df
