from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
import pdfplumber
import re
import tempfile
import os
from auth.dependencies import get_current_user

router = APIRouter(
    prefix="/improvement",
    tags=["Resume Improvement"]
)

# =================================================
# CONSTANTS
# =================================================

MAX_PAGES = 5  # ✅ LIMIT PDF PAGES (huge memory saver)

REQUIRED_SECTIONS = {
    "summary": ("summary", "profile", "objective"),
    "skills": ("skills", "technical skills"),
    "projects": ("projects", "project"),
    "experience": ("experience", "work experience", "internship"),
    "education": ("education", "academic")
}

WEAK_PHRASES = (
    "worked on", "responsible for",
    "helped with", "good knowledge",
    "basic knowledge"
)

ACTION_VERBS = (
    "built", "developed", "designed", "implemented",
    "optimized", "created", "engineered",
    "integrated", "deployed"
)

SKILL_VOCAB = (
    "react", "javascript", "node", "nodejs", "express",
    "mongodb", "python", "machine learning", "sql",
    "html", "css", "angular", "docker", "aws",
    "rest", "api", "socket", "firebase"
)

STACK_MAP = {
    "mern": ("mongodb", "express", "react", "node"),
    "mean": ("mongodb", "express", "angular", "node")
}

BULLET_REGEX = re.compile(r"(?:•|-|–|\*|\d+\.)\s*(.+)")
YEAR_REGEX = re.compile(r"(\d+)\+?\s*years?")
EXP_REGEX = re.compile(r"(\d+)\s*(?:years?|months?)")

# =================================================
# UTILS (OPTIMIZED)
# =================================================

def normalize_text(text: str) -> str:
    return " ".join(text.lower().split())


def extract_text_from_pdf(pdf_path: str) -> str:
    texts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages[:MAX_PAGES]:  # ✅ LIMIT PAGES
            page_text = page.extract_text()
            if page_text:
                texts.append(page_text)
    return "\n".join(texts)


def extract_bullets(text: str):
    return BULLET_REGEX.findall(text)


# =================================================
# SKILL GAP
# =================================================

def extract_skills(text: str):
    skills = set(s for s in SKILL_VOCAB if s in text)
    for stack, expanded in STACK_MAP.items():
        if stack in text:
            skills.update(expanded)
    return skills


def compute_missing_skills(resume_text: str, jd_text: str):
    return list(extract_skills(jd_text) - extract_skills(resume_text))


# =================================================
# EXPERIENCE
# =================================================

def extract_experience_requirement(jd_text):
    match = YEAR_REGEX.search(jd_text)
    return int(match.group(1)) if match else None


def resume_experience_years(resume_text):
    matches = EXP_REGEX.findall(resume_text)
    return max(map(int, matches)) if matches else 0


def experience_requirement_suggestions(resume_text, jd_text):
    jd_years = extract_experience_requirement(jd_text)
    resume_years = resume_experience_years(resume_text)

    if jd_years and resume_years < jd_years:
        return [
            f"The job requires {jd_years}+ years of experience. "
            f"Add internships, freelance, or professional experience with duration."
        ]
    return []


# =================================================
# IMPROVEMENTS
# =================================================

def missing_section_suggestions(text):
    return [
        f"Add a '{section.capitalize()}' section to improve resume completeness."
        for section, keys in REQUIRED_SECTIONS.items()
        if not any(k in text for k in keys)
    ]


def soft_section_suggestions(text):
    if "summary" in text:
        summary_block = text.split("summary", 1)[1][:300]
        if len(summary_block.split()) < 40:
            return ["Expand your summary to 2–3 lines highlighting skills and experience."]
    return []


def skill_gap_suggestions(missing_skills):
    return (
        [f"Add {skill} by mentioning it in a project or hands-on experience."]
        if missing_skills else
        ["Strengthen your profile by adding measurable impact to your projects."]
    )


def weak_bullet_suggestions(original_text):
    bullets = extract_bullets(original_text)
    suggestions = []

    for bullet in bullets:
        low = bullet.lower()
        if any(p in low for p in WEAK_PHRASES):
            suggestions.append({
                "original": bullet,
                "suggested": (
                    "Use action verb + technology + result. "
                    "Example: 'Developed REST APIs using Node.js and Express.js.'"
                )
            })

    return suggestions or [{
        "original": "Bullets are fine",
        "suggested": "Add numbers (users, performance, scale) for more impact."
    }]


def grammar_suggestions(text):
    tips = [f"Replace weak phrase '{p}' with strong action verbs." for p in WEAK_PHRASES if p in text]
    return tips or ["Grammar is good. Minor refinements can improve clarity."]


def skill_section_suggestions(text):
    if "skills" not in text:
        return []
    block = text.split("skills", 1)[1][:400]
    skills = [s for s in re.split(r",|\n", block) if s.strip()]

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
    resume_clean = normalize_text(resume_text)
    jd_clean = normalize_text(jd_text)

    missing_skills = compute_missing_skills(resume_clean, jd_clean)

    return {
        "critical_improvements": (
            missing_section_suggestions(resume_clean)
            + soft_section_suggestions(resume_clean)
            + experience_requirement_suggestions(resume_clean, jd_clean)
        ),
        "skill_gap_suggestions": skill_gap_suggestions(missing_skills),
        "bullet_point_improvements": weak_bullet_suggestions(resume_text),
        "grammar_tips": grammar_suggestions(resume_clean),
        "skill_section_tips": skill_section_suggestions(resume_clean),
        "project_section_tips": project_section_suggestions(resume_clean),
        "detected_missing_skills": missing_skills
    }


# =================================================
# API
# =================================================

@router.post("/suggestions")
async def resume_improvements(
    resume: UploadFile = File(...),
    job_description: str = Form(...),
    current_user: str = Depends(get_current_user)
):
    if not resume.filename.lower().endswith(".pdf"):
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
