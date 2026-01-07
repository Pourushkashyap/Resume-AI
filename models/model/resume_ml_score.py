from fastapi import APIRouter, UploadFile, File, HTTPException
import pdfplumber
import joblib
import re
import os
import tempfile
from fastapi import Depends
from auth.dependencies import get_current_user


router = APIRouter(
    prefix="/ml-score",
    tags=["Resume ML Score"]
)

# Load trained model ONCE
MODEL_PATH = "models/resume_score_model.pkl"
model = joblib.load(MODEL_PATH)

SKILL_VOCAB = [
    "react", "javascript", "node", "express", "mongodb",
    "python", "sql", "html", "css", "machine learning",
    "docker", "aws", "api", "rest"
]

WEAK_PHRASES = [
    "worked on",
    "responsible for",
    "helped with",
    "basic knowledge",
    "good knowledge"
]


def extract_features(text: str):
    text = text.lower()

    resume_length = len(text.split())
    num_skills = sum(1 for skill in SKILL_VOCAB if skill in text)
    num_projects = text.count("project")
    num_bullets = len(re.findall(r"(?:•|-|–|\*)", text))

    experience_years = 0
    matches = re.findall(r"(\d+)\s*(?:years?|months?)", text)
    if matches:
        experience_years = max(map(int, matches))

    grammar_issues = sum(text.count(p) for p in WEAK_PHRASES)

    return [[
        resume_length,
        num_skills,
        num_projects,
        num_bullets,
        experience_years,
        grammar_issues
    ]]


def extract_text_from_pdf(path):
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            if page.extract_text():
                text += page.extract_text() + "\n"
    return text


@router.post("/predict")
async def predict_resume_score(
    resume: UploadFile = File(...),
    current_user: str = Depends(get_current_user)
):
    if not resume.filename.endswith(".pdf"):
        raise HTTPException(400, "Only PDF allowed")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await resume.read())
        path = tmp.name

    try:
        text = extract_text_from_pdf(path)
        features = extract_features(text)
        score = model.predict(features)[0]

        return {
            "ml_resume_score": round(float(score), 2)
        }
    finally:
        os.remove(path)

