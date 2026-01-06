import pdfplumber
import re
import nltk
from nltk.corpus import stopwords
from fastapi import FastAPI, UploadFile, File, Form
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import tempfile, os


nltk.download("stopwords")
STOPWORDS = set(stopwords.words("english"))

app = FastAPI(title="Industry-Grade ATS Resume System")


def extract_text_from_pdf(path):
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
    if not text.strip():
        raise ValueError("PDF contains no readable text")
    return text


def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return " ".join(w for w in text.split() if w not in STOPWORDS)


def extract_sections(text):
    sections = {"skills": "", "projects": "", "experience": ""}
    current = None

    for word in text.split():
        if word in ["skills", "technical"]:
            current = "skills"
        elif word in ["projects", "project"]:
            current = "projects"
        elif word in ["experience", "internship"]:
            current = "experience"

        if current:
            sections[current] += word + " "

    return sections


SKILL_VOCAB = [
    "react", "javascript", "node", "nodejs", "express",
    "mongodb", "python", "machine learning", "sql",
    "html", "css", "angular"
]

STACK_MAP = {
    "mern": ["mongodb", "express", "react", "node"],
    "mean": ["mongodb", "express", "angular", "node"],
    "frontend": ["react", "javascript", "html", "css"],
    "backend": ["node", "express"],
    "data science": ["python", "machine learning"]
}

def extract_skills(text):
    skills = set()
    for s in SKILL_VOCAB:
        if s in text:
            skills.add(s)
    for stack, expanded in STACK_MAP.items():
        if stack in text:
            skills.update(expanded)
    return skills


def skill_gap_detection(resume_skills, jd_skills):
    resume_set = set(resume_skills)
    jd_set = set(jd_skills)

    return {
        "matched_skills": list(resume_set & jd_set),
        "missing_skills": list(jd_set - resume_set),
        "extra_skills": list(resume_set - jd_set)
    }


def skill_match_score(resume_skills, jd_skills):
    if not jd_skills:
        return 0.0
    return len(resume_skills & jd_skills) / len(jd_skills)



def project_relevance_score(project_text, jd_skills):
    """
    Industry-style project relevance:
    - Based on skill coverage
    - NOT sentence similarity
    """

    if not project_text.strip() or not jd_skills:
        return 0.0

    project_text = project_text.lower()

    used_skills = set()
    for skill in jd_skills:
        if skill in project_text:
            used_skills.add(skill)

    
    coverage_ratio = len(used_skills) / len(jd_skills)

    
    project_count_bonus = 0.1 if project_text.count("project") >= 2 else 0.0
    complexity_bonus = 0.1 if any(
        kw in project_text
        for kw in ["api", "real time", "socket", "database", "authentication"]
    ) else 0.0

    final_score = min(1.0, coverage_ratio + project_count_bonus + complexity_bonus)
    return final_score



def text_similarity(a, b):
    if not a.strip() or not b.strip():
        return 0.0
    vectorizer = TfidfVectorizer(ngram_range=(1, 2))
    vectors = vectorizer.fit_transform([a, b])
    return cosine_similarity(vectors[0], vectors[1])[0][0]




@app.post("/match-resume")
async def match_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(...)
):
   
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await resume.read())
        resume_path = tmp.name

    raw_resume = extract_text_from_pdf(resume_path)
    os.remove(resume_path)

    resume_text = clean_text(raw_resume)
    jd_text = clean_text(job_description)

    resume_sections = extract_sections(resume_text)

    resume_skills = extract_skills(resume_text)
    jd_skills = extract_skills(jd_text)

    
    skill_score = skill_match_score(resume_skills, jd_skills)
    project_score = project_relevance_score(resume_sections["projects"], jd_skills)
    experience_score = text_similarity(resume_sections["experience"], jd_text)

    final_score = (
        0.5 * skill_score +
        0.3 * project_score +
        0.2 * experience_score
    ) * 100

    final_score = round(final_score, 2)

    verdict = (
        "STRONG MATCH" if final_score >= 75 else
        "MODERATE MATCH" if final_score >= 55 else
        "WEAK MATCH"
    )

    
    gap = skill_gap_detection(resume_skills, jd_skills)

    response = {
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

    if not jd_skills:
        response["skill_gap_note"] = (
            "Job description does not explicitly list technical skills."
        )

    return response



# uvicorn file_name:app --reload
