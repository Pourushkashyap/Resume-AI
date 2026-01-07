from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
import pdfplumber
import joblib
import re
import os
import tempfile
from auth.dependencies import get_current_user

router = APIRouter(
    prefix="/ml-score",
    tags=["Resume ML Score"]
)

# =================================================
# CONSTANTS (MEMORY SAFE)
# =================================================

MAX_PAGES = 5              # 🔥 Big memory saver
MAX_TEXT_CHARS = 15000     # 🔥 Prevent huge input

MODEL_PATH = os.getenv(
    "ML_MODEL_PATH",
    "models/resume_score_model.pkl"
)

# Load model ONCE (safe)
try:
    model = joblib.load(MODEL_PATH)
except Exception as e:
    raise RuntimeError(f"Failed to load ML model: {e}")

SKILL_VOCAB = {
    "react","javascript","node","express","mongodb",
    "python","sql","html","css","machine learning",
    "docker","aws","api","rest"
}

WEAK_PHRASES = {
    "worked on",
    "responsible for",
    "helped with",
    "basic knowledge",
    "good knowledge"
}

BULLET_REGEX = re.compile(r"(?:•|-|–|\*)")
EXP_REGEX = re.compile(r"(\d+)\s*(?:years?|months?)")

# =================================================
# UTILS
# =================================================

def extract_text_from_pdf(path: str) -> str:
    texts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages[:MAX_PAGES]:
            t = page.extract_text()
            if t:
                texts.append(t)

    text = "\n".join(texts)
    return text[:MAX_TEXT_CHARS]  # 🔥 cap size


def extract_features(text: str):
    text = text.lower()

    resume_length = len(text.split())
    num_skills = sum(1 for s in SKILL_VOCAB if s in text)
    num_projects = text.count("project")
    num_bullets = len(BULLET_REGEX.findall(text))

    matches = EXP_REGEX.findall(text)
    experience_years = max(map(int, matches)) if matches else 0

    grammar_issues = sum(text.count(p) for p in WEAK_PHRASES)

    return [[
        resume_length,
        num_skills,
        num_projects,
        num_bullets,
        experience_years,
        grammar_issues
    ]]

# =================================================
# API
# =================================================

@router.post("/predict")
async def predict_resume_score(
    resume: UploadFile = File(...),
    current_user: str = Depends(get_current_user)
):
    if not resume.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF allowed")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await resume.read())
        path = tmp.name

    try:
        text = extract_text_from_pdf(path)
        if not text.strip():
            raise HTTPException(400, "Unable to extract resume text")

        features = extract_features(text)
        score = model.predict(features)[0]

        return {
            "ml_resume_score": round(float(score), 2)
        }

    finally:
        os.remove(path)
