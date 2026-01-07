from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
import pdfplumber
import re
import tempfile
import os
from models.auth.dependencies import get_current_user

router = APIRouter(
    prefix="/quality",
    tags=["Resume Quality"]
)

# =================================================
# LIMITS (RENDER SAFE)
# =================================================
MAX_PAGES = 5
MAX_TEXT_CHARS = 15000

# =================================================
# PRE-COMPILED REGEX
# =================================================
SPACE_REGEX = re.compile(r"\s+")
SENTENCE_SPLIT_REGEX = re.compile(r"[.!?]")
BULLET_REGEX = re.compile(r"(?:•|-|–|\*|\d+\.)")

# =================================================
# CONSTANTS
# =================================================
REQUIRED_SECTIONS = {
    "summary": ["summary", "profile", "objective"],
    "skills": ["skills", "technical skills"],
    "projects": ["projects", "project"],
    "experience": ["experience", "work experience", "internship"],
    "education": ["education", "academic"]
}

WEAK_PHRASES = {
    "worked on",
    "responsible for",
    "helped with",
    "good knowledge",
    "basic knowledge",
    "i was",
    "i have"
}

ACTION_VERBS = {
    "built", "developed", "designed", "implemented",
    "optimized", "created", "engineered",
    "integrated", "deployed"
}

# =================================================
# UTILS
# =================================================
def normalize_text(text: str) -> str:
    text = text.lower()
    return SPACE_REGEX.sub(" ", text).strip()


def extract_text_from_pdf(path: str) -> str:
    texts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages[:MAX_PAGES]:
            t = page.extract_text()
            if t:
                texts.append(t)

    text = "\n".join(texts)
    return text[:MAX_TEXT_CHARS]


# =================================================
# SCORING MODULES
# =================================================
def interpret_score(score: float) -> str:
    if score >= 85:
        return "Excellent resume quality"
    if score >= 70:
        return "Good resume with minor improvements needed"
    if score >= 55:
        return "Average resume, needs improvement"
    return "Poor resume quality"


def section_completeness_score(text: str) -> float:
    found = 0
    for keys in REQUIRED_SECTIONS.values():
        if any(k in text for k in keys):
            found += 1
    return (found / len(REQUIRED_SECTIONS)) * 100


def grammar_quality_score(text: str) -> float:
    sentences = [s for s in SENTENCE_SPLIT_REGEX.split(text) if s.strip()]
    avg_len = (
        sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
    )

    weak_count = sum(text.count(p) for p in WEAK_PHRASES)

    score = 100
    if avg_len > 28:
        score -= 10
    if weak_count > 3:
        score -= 15

    return max(score, 50)


def bullet_quality_score(original_text: str) -> float:
    bullets = BULLET_REGEX.findall(original_text)

    if not bullets:
        return 60

    good = sum(
        1 for b in bullets
        if any(v in b.lower() for v in ACTION_VERBS)
    )

    return (good / len(bullets)) * 100


def skill_structure_score(text: str) -> float:
    skill_block = ""
    for key in REQUIRED_SECTIONS["skills"]:
        if key in text:
            skill_block = text.split(key, 1)[1][:400]
            break

    skills = [s.strip() for s in re.split(r",|\n", skill_block) if s.strip()]
    count = len(skills)

    if count < 5:
        return 50
    if count > 25:
        return 65
    return 90


def formatting_score(text: str) -> float:
    words = len(text.split())
    if words < 300:
        return 60
    if words > 1200:
        return 65
    return 90


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

# =================================================
# API
# =================================================
@router.post("/score")
async def resume_quality_score(
    resume: UploadFile = File(...),
    current_user: str = Depends(get_current_user)
):
    if not resume.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF resumes are supported")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await resume.read())
        path = tmp.name

    try:
        text = extract_text_from_pdf(path)
        if not text.strip():
            raise HTTPException(400, "Unable to extract text from PDF")

        return compute_resume_quality_score(text)

    finally:
        os.remove(path)
