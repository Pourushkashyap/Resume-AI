from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import pdfplumber, tempfile, os, re

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


router = APIRouter(
    prefix="/semantic",
    tags=["Semantic Matching"]
)

# Load semantic model
model = SentenceTransformer("all-MiniLM-L6-v2")


# -----------------------------
# Helpers
# -----------------------------
def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            if page.extract_text():
                text += page.extract_text() + "\n"
    return text.lower()


def semantic_similarity(a, b):
    va = model.encode(a)
    vb = model.encode(b)
    return float(cosine_similarity([va], [vb])[0][0])


# -----------------------------
# Requirement Extraction
# -----------------------------
def extract_experience_requirement(jd):
    match = re.search(r"(\d+)\+?\s+years", jd)
    if match:
        return int(match.group(1))
    return None


def extract_project_requirement(jd):
    if "project" in jd:
        return "project based development"
    return None


def extract_responsibility_requirements(jd):
    keywords = [
        "design", "develop", "deploy", "optimize",
        "maintain", "collaborate", "lead", "scale"
    ]
    return [k for k in keywords if k in jd]


def extract_domain(jd):
    domains = [
        "finance", "healthcare", "ecommerce",
        "banking", "education", "ai", "ml"
    ]
    for d in domains:
        if d in jd:
            return d
    return None


# -----------------------------
# GAP DETECTORS
# -----------------------------
def detect_experience_gap(resume, jd):
    required_years = extract_experience_requirement(jd)
    if not required_years:
        return None

    resume_years = re.findall(r"(\d+)\s+years", resume)
    resume_years = max(map(int, resume_years)) if resume_years else 0

    if resume_years < required_years:
        return f"JD requires {required_years}+ years, resume shows {resume_years}"
    return None


def detect_project_gap(resume, jd):
    req = extract_project_requirement(jd)
    if not req:
        return None

    sim = semantic_similarity("hands-on real world projects", resume)
    if sim < 0.55:
        return "JD expects strong project experience"
    return None


def detect_responsibility_gap(resume, jd):
    gaps = []
    responsibilities = extract_responsibility_requirements(jd)

    for r in responsibilities:
        sim = semantic_similarity(f"experience to {r} systems", resume)
        if sim < 0.50:
            gaps.append(f"Missing responsibility: {r}")

    return gaps if gaps else None


def detect_domain_gap(resume, jd):
    domain = extract_domain(jd)
    if not domain:
        return None

    sim = semantic_similarity(f"{domain} domain experience", resume)
    if sim < 0.55:
        return f"No clear {domain} domain experience"
    return None


# -----------------------------
# SKILL GAP DETECTION (SEMANTIC + ALIAS)
# -----------------------------
SKILL_ALIASES = {
    "rest api": ["rest api", "restful api", "apis", "api development"],
    "react": ["react", "reactjs", "frontend react"],
    "node": ["node", "nodejs", "node.js"],
    "mongodb": ["mongodb", "mongo"],
    "express": ["express", "express.js"],
    "docker": ["docker", "containers", "containerization"],
    "aws": ["aws", "amazon web services", "ec2", "s3"]
}


def semantic_skill_gap(resume: str, jd: str):
    resume_lower = resume.lower()
    jd_lower = jd.lower()
    missing = []

    for skill, aliases in SKILL_ALIASES.items():
        # Skill is required by JD
        if skill in jd_lower:

            # 1️⃣ Exact or alias match
            if any(alias in resume_lower for alias in aliases):
                continue

            # 2️⃣ Semantic fallback
            context = f"experience with {skill}"
            similarity = semantic_similarity(context, resume)

            if similarity < 0.55:
                missing.append(skill)

    return missing







def full_gap_analysis(resume, jd):
    semantic_score = semantic_similarity(resume, jd) * 100

    verdict = (
        "STRONG MATCH" if semantic_score >= 70 else
        "MODERATE MATCH" if semantic_score >= 50 else
        "WEAK MATCH"
    )

    return {
        "semantic_match_score": round(semantic_score, 2),
        "verdict": verdict,

        # 1️⃣ Skill Gap
        "missing_skills": semantic_skill_gap(resume, jd),

        # 2️⃣ Experience Gap
        "missing_experience": detect_experience_gap(resume, jd),

        # 3️⃣ Project Gap
        "missing_projects": detect_project_gap(resume, jd),

        # 4️⃣ Responsibility Gap
        "missing_responsibilities": detect_responsibility_gap(resume, jd),

        # 5️⃣ Domain Gap
        "missing_domain": detect_domain_gap(resume, jd)
    }


# -----------------------------
# API
# -----------------------------
@router.post("/full-gap-analysis")
async def analyze(
    resume: UploadFile = File(...),
    job_description: str = Form(...)
):
    if not resume.filename.endswith(".pdf"):
        raise HTTPException(400, "Only PDF allowed")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await resume.read())
        path = tmp.name

    try:
        resume_text = extract_text_from_pdf(path)
        result = full_gap_analysis(resume_text, job_description.lower())
        return {"status": "success", **result}
    finally:
        os.remove(path)
