from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import pdfplumber
import re
import tempfile
import os
from fastapi import Depends
from auth.dependencies import get_current_user


router = APIRouter(
    prefix="/improvement",
    tags=["Resume Improvement"]
)


REQUIRED_SECTIONS = {
    "summary": ["summary", "profile", "objective"],
    "skills": ["skills", "technical skills"],
    "projects": ["projects", "project"],
    "experience": ["experience", "work experience", "internship"],
    "education": ["education", "academic"]
}

WEAK_PHRASES = [
    "worked on",
    "responsible for",
    "helped with",
    "good knowledge",
    "basic knowledge"
]

ACTION_VERBS = [
    "built", "developed", "designed", "implemented",
    "optimized", "created", "engineered",
    "integrated", "deployed"
]

SKILL_VOCAB = [
    "react", "javascript", "node", "nodejs", "express",
    "mongodb", "python", "machine learning", "sql",
    "html", "css", "angular", "docker", "aws",
    "rest", "api", "socket", "firebase"
]

STACK_MAP = {
    "mern": ["mongodb", "express", "react", "node"],
    "mean": ["mongodb", "express", "angular", "node"]
}

# =================================================
# UTILS
# =================================================

def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
    return text


def extract_bullets(text: str):
    return re.findall(r"(?:•|-|–|\*|\d+\.)\s*(.+)", text)


# =================================================
# SKILL GAP LOGIC
# =================================================

def extract_skills(text: str):
    skills = set()
    for s in SKILL_VOCAB:
        if s in text:
            skills.add(s)
    for stack, expanded in STACK_MAP.items():
        if stack in text:
            skills.update(expanded)
    return skills


def compute_missing_skills(resume_text: str, jd_text: str):
    return list(extract_skills(jd_text) - extract_skills(resume_text))


# =================================================
# EXPERIENCE LOGIC (IMPROVED)
# =================================================

def extract_experience_requirement(jd_text):
    match = re.search(r"(\d+)\+?\s*years?", jd_text)
    years = int(match.group(1)) if match else None
    return years


def resume_experience_years(resume_text):
    matches = re.findall(r"(\d+)\s*(?:years?|months?)", resume_text)
    if not matches:
        return 0
    return max(int(m) for m in matches)


def experience_requirement_suggestions(resume_text, jd_text):
    suggestions = []
    jd_years = extract_experience_requirement(jd_text)
    resume_years = resume_experience_years(resume_text)

    if jd_years and resume_years < jd_years:
        suggestions.append(
            f"The job description requires {jd_years}+ years of experience, "
            f"but your resume does not clearly demonstrate this. "
            f"Add internship, freelance, or professional experience with duration."
        )

    return suggestions


# =================================================
# IMPROVEMENT MODULES
# =================================================

def missing_section_suggestions(text):
    return [
        f"Add a '{section.capitalize()}' section to improve resume completeness."
        for section, keys in REQUIRED_SECTIONS.items()
        if not any(k in text for k in keys)
    ]


def soft_section_suggestions(text):
    tips = []
    if "summary" in text:
        summary_block = text.split("summary", 1)[1][:300]
        if len(summary_block.split()) < 40:
            tips.append(
                "Expand your summary to 2–3 lines highlighting skills and experience."
            )
    return tips


def skill_gap_suggestions(missing_skills):
    if not missing_skills:
        return [
            "Strengthen your profile by adding measurable impact to your projects."
        ]
    return [
        f"Add {skill} by mentioning it in a project or hands-on experience."
        for skill in missing_skills
    ]


def weak_bullet_suggestions(original_text):
    bullets = extract_bullets(original_text)
    suggestions = []

    for bullet in bullets:
        if any(p in bullet.lower() for p in WEAK_PHRASES):
            suggestions.append({
                "original": bullet,
                "suggested": (
                    "Rewrite with action verb + technology + outcome. "
                    "Example: 'Developed REST APIs using Node.js and Express.js.'"
                )
            })

    if bullets and not suggestions:
        suggestions.append({
            "original": "Your bullets are clear",
            "suggested": "Add numbers (users, speed, scale) to increase impact."
        })

    return suggestions


def grammar_suggestions(text):
    tips = [
        f"Replace weak phrase '{p}' with strong action verbs."
        for p in WEAK_PHRASES if p in text
    ]
    if not tips:
        tips.append("Grammar is good. Minor refinements can improve clarity.")
    return tips


def skill_section_suggestions(text):
    if "skills" not in text:
        return []
    block = text.split("skills", 1)[1][:400]
    skills = [s.strip() for s in re.split(r",|\n", block) if s.strip()]

    if len(skills) < 5:
        return ["Add more relevant technical skills."]
    if len(skills) > 25:
        return ["Group skills into categories for better readability."]
    return []


def project_section_suggestions(text):
    if "projects" not in text:
        return ["Add at least 2 real-world projects."]
    block = text.split("projects", 1)[1][:500]
    if not any(v in block for v in ACTION_VERBS):
        return ["Start project bullets with action verbs and tools used."]
    return []


# =================================================
# MAIN ENGINE
# =================================================

def generate_resume_improvements(resume_text, jd_text):
    clean_resume = normalize_text(resume_text)
    clean_jd = normalize_text(jd_text)

    missing_skills = compute_missing_skills(clean_resume, clean_jd)

    return {
        "critical_improvements": (
            missing_section_suggestions(clean_resume)
            + soft_section_suggestions(clean_resume)
            + experience_requirement_suggestions(clean_resume, clean_jd)
        ),
        "skill_gap_suggestions": skill_gap_suggestions(missing_skills),
        "bullet_point_improvements": weak_bullet_suggestions(resume_text),
        "grammar_tips": grammar_suggestions(clean_resume),
        "skill_section_tips": skill_section_suggestions(clean_resume),
        "project_section_tips": project_section_suggestions(clean_resume),
        "detected_missing_skills": missing_skills
    }


# =================================================
# API ENDPOINT
# =================================================

@router.post("/suggestions")
async def resume_improvements(
    resume: UploadFile = File(...),
    job_description: str = Form(...),
    current_user: str = Depends(get_current_user)
):
    if not resume.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF resumes are supported")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await resume.read())
        tmp_path = tmp.name

    try:
        resume_text = extract_text_from_pdf(tmp_path)
        if not resume_text.strip():
            raise HTTPException(status_code=400, detail="Unable to extract resume text")
        return generate_resume_improvements(resume_text, job_description)
    finally:
        os.remove(tmp_path)
