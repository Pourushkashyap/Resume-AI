import pdfplumber
import re
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import tempfile, os

app = FastAPI(title="Industry-Grade ATS Resume System")

# =================================================
# CONSTANTS (MEMORY SAFE)
# =================================================

MAX_PAGES = 5  # 🔥 BIG memory saver

STOPWORDS = {
    "the","is","are","a","an","and","or","to","of","in","for",
    "on","with","as","by","at","from","this","that","it"
}

SKILL_VOCAB = {
    "react","javascript","node","nodejs","express",
    "mongodb","python","machine learning","sql",
    "html","css","angular"
}

STACK_MAP = {
    "mern": {"mongodb","express","react","node"},
    "mean": {"mongodb","express","angular","node"},
    "frontend": {"react","javascript","html","css"},
    "backend": {"node","express"},
    "data science": {"python","machine learning"}
}

NON_ALPHA = re.compile(r"[^a-z0-9\s]")
MULTI_SPACE = re.compile(r"\s+")

# =================================================
# UTILS
# =================================================

def extract_text_from_pdf(path: str) -> str:
    texts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages[:MAX_PAGES]:  # 🔥 limit pages
            t = page.extract_text()
            if t:
                texts.append(t)
    text = "\n".join(texts)
    if not text.strip():
        raise ValueError("PDF contains no readable text")
    return text


def clean_text(text: str) -> str:
    text = text.lower()
    text = NON_ALPHA.sub(" ", text)
    text = MULTI_SPACE.sub(" ", text)
    return " ".join(w for w in text.split() if w not in STOPWORDS)


def extract_sections(text: str):
    sections = {"skills": "", "projects": "", "experience": ""}
    current = None

    for word in text.split():
        if word in {"skills","technical"}:
            current = "skills"
        elif word in {"projects","project"}:
            current = "projects"
        elif word in {"experience","internship"}:
            current = "experience"

        if current:
            sections[current] += word + " "

    return sections


# =================================================
# SKILLS
# =================================================

def extract_skills(text: str):
    skills = {s for s in SKILL_VOCAB if s in text}
    for stack, expanded in STACK_MAP.items():
        if stack in text:
            skills.update(expanded)
    return skills


def skill_gap_detection(resume_skills, jd_skills):
    return {
        "matched_skills": list(resume_skills & jd_skills),
        "missing_skills": list(jd_skills - resume_skills),
        "extra_skills": list(resume_skills - jd_skills)
    }


def skill_match_score(resume_skills, jd_skills):
    return len(resume_skills & jd_skills) / len(jd_skills) if jd_skills else 0.0


# =================================================
# PROJECT SCORE (LIGHTWEIGHT)
# =================================================

def project_relevance_score(project_text, jd_skills):
    if not project_text or not jd_skills:
        return 0.0

    used = {s for s in jd_skills if s in project_text}

    coverage = len(used) / len(jd_skills)

    bonus = 0.0
    if project_text.count("project") >= 2:
        bonus += 0.1
    if any(k in project_text for k in ("api","socket","database","auth")):
        bonus += 0.1

    return min(1.0, coverage + bonus)


# =================================================
# EXPERIENCE (SAFE TF-IDF)
# =================================================

def text_similarity(a: str, b: str):
    if not a or not b:
        return 0.0

    vectorizer = TfidfVectorizer(
        max_features=500,  # 🔥 memory limit
        ngram_range=(1, 2)
    )
    vectors = vectorizer.fit_transform([a, b])
    return cosine_similarity(vectors[0], vectors[1])[0][0]


# =================================================
# API
# =================================================

@app.post("/match-resume")
async def match_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(...)
):
    if not resume.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF allowed")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await resume.read())
        path = tmp.name

    try:
        raw_resume = extract_text_from_pdf(path)
    finally:
        os.remove(path)

    resume_text = clean_text(raw_resume)
    jd_text = clean_text(job_description)

    resume_sections = extract_sections(resume_text)

    resume_skills = extract_skills(resume_text)
    jd_skills = extract_skills(jd_text)

    skill_score = skill_match_score(resume_skills, jd_skills)
    project_score = project_relevance_score(resume_sections["projects"], jd_skills)
    experience_score = text_similarity(resume_sections["experience"], jd_text)

    final_score = round(
        (0.5 * skill_score + 0.3 * project_score + 0.2 * experience_score) * 100,
        2
    )

    verdict = (
        "STRONG MATCH" if final_score >= 75 else
        "MODERATE MATCH" if final_score >= 55 else
        "WEAK MATCH"
    )

    gap = skill_gap_detection(resume_skills, jd_skills)

    return {
        "core_skills_matched": gap["matched_skills"],
        "missing_skills": gap["missing_skills"],
        "extra_skills_detected": gap["extra_skills"],
        "skill_match_percent": round(skill_score * 100, 2),
        "project_relevance": round(project_score * 100, 2),
        "experience_relevance": round(experience_score * 100, 2),
        "ats_match_score": final_score,
        "verdict": verdict,
        "note": "Extra skills are treated as strengths, not penalties"
    }
