from fastapi import APIRouter, UploadFile, File, HTTPException
import pdfplumber
import re
import tempfile
import os
from fastapi import Depends
from models.auth.dependencies import get_current_user


router = APIRouter(
    prefix="/quality",
    tags=["Resume Quality"]
)
# -------------------------------------------------
# TEXT NORMALIZATION
# -------------------------------------------------
def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# -------------------------------------------------
# HUMAN READABLE INTERPRETATION
# -------------------------------------------------
def interpret_score(score: float) -> str:
    if score >= 85:
        return "Excellent resume quality"
    if score >= 70:
        return "Good resume with minor improvements needed"
    if score >= 55:
        return "Average resume, needs improvement"
    return "Poor resume quality"


# -------------------------------------------------
# SECTION COMPLETENESS
# -------------------------------------------------
REQUIRED_SECTIONS = {
    "summary": ["summary", "profile", "objective"],
    "skills": ["skills", "technical skills"],
    "projects": ["projects", "project"],
    "experience": ["experience", "work experience", "internship"],
    "education": ["education", "academic"]
}

def section_completeness_score(text: str) -> float:
    found = 0
    for keywords in REQUIRED_SECTIONS.values():
        if any(k in text for k in keywords):
            found += 1
    return (found / len(REQUIRED_SECTIONS)) * 100


# -------------------------------------------------
# GRAMMAR & LANGUAGE QUALITY (RULE-BASED)
# -------------------------------------------------
WEAK_PHRASES = [
    "worked on",
    "responsible for",
    "helped with",
    "good knowledge",
    "basic knowledge",
    "i was",
    "i have"
]

def grammar_quality_score(text: str) -> float:
    sentences = re.split(r"[.!?]", text)
    sentences = [s.strip() for s in sentences if s.strip()]

    avg_sentence_len = (
        sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
    )

    weak_phrase_count = sum(text.count(p) for p in WEAK_PHRASES)

    score = 100

    if avg_sentence_len > 28:
        score -= 10  # capped penalty

    if weak_phrase_count > 3:
        score -= 15

    return max(score, 50)  # hard floor (industry rule)


# -------------------------------------------------
# BULLET POINT QUALITY (IMPROVED)
# -------------------------------------------------
ACTION_VERBS = [
    "built", "developed", "designed", "implemented",
    "optimized", "created", "engineered",
    "integrated", "deployed"
]

def bullet_quality_score(original_text: str) -> float:
    bullets = re.findall(
        r"(?:•|-|–|\*|\d+\.)\s*(.+)",
        original_text
    )

    if not bullets:
        return 60

    good = 0
    for bullet in bullets:
        bullet = bullet.lower()
        if any(verb in bullet for verb in ACTION_VERBS):
            good += 1

    return (good / len(bullets)) * 100


# -------------------------------------------------
# SKILL STRUCTURE QUALITY
# -------------------------------------------------
def skill_structure_score(text: str) -> float:
    skill_section = ""

    for key in REQUIRED_SECTIONS["skills"]:
        if key in text:
            skill_section = text.split(key, 1)[1][:400]
            break

    skills = re.split(r",|\n", skill_section)
    skills = [s.strip() for s in skills if len(s.strip()) > 1]

    count = len(skills)

    if count < 5:
        return 50
    if count > 25:
        return 65
    return 90


# -------------------------------------------------
# FORMATTING & LENGTH QUALITY
# -------------------------------------------------
def formatting_score(text: str) -> float:
    word_count = len(text.split())

    if word_count < 300:
        return 60
    if word_count > 1200:
        return 65
    return 90


# -------------------------------------------------
# FINAL RESUME QUALITY SCORE
# -------------------------------------------------
def compute_resume_quality_score(resume_text: str) -> dict:
    clean = normalize_text(resume_text)

    section_score = section_completeness_score(clean)
    grammar_score = grammar_quality_score(clean)
    bullet_score = bullet_quality_score(resume_text)
    skill_score = skill_structure_score(clean)
    format_score = formatting_score(clean)

    final_score = (
        0.25 * section_score +
        0.25 * grammar_score +
        0.20 * bullet_score +
        0.15 * skill_score +
        0.15 * format_score
    )

    return {
        "resume_score": round(final_score, 2),
        "section_completeness": round(section_score, 2),
        "grammar_quality": round(grammar_score, 2),
        "bullet_quality": round(bullet_score, 2),
        "skill_structure": round(skill_score, 2),
        "formatting_quality": round(format_score, 2),
        "interpretation": interpret_score(final_score)
    }


# -------------------------------------------------
# FASTAPI ENDPOINT
# -------------------------------------------------
@router.post("/score")
async def resume_quality_score(
    resume: UploadFile = File(...),
    current_user: str = Depends(get_current_user)
):
    if not resume.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF resumes are supported")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await resume.read())
        tmp_path = tmp.name

    try:
        text = ""
        with pdfplumber.open(tmp_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"

        if not text.strip():
            raise HTTPException(status_code=400, detail="Unable to extract text from PDF")

        return compute_resume_quality_score(text)
    finally:
        os.remove(tmp_path)

