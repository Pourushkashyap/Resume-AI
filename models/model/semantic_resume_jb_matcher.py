# from fastapi import APIRouter, UploadFile, File, Form, HTTPException
# import pdfplumber, tempfile, os, re
# from sentence_transformers import SentenceTransformer
# from sklearn.metrics.pairwise import cosine_similarity

# router = APIRouter(
#     prefix="/semantic",
#     tags=["Semantic Matching"]
# )

# # ===============================
# # SAFETY LIMITS (RENDER SAFE)
# # ===============================
# MAX_PAGES = 4
# MAX_TEXT_CHARS = 4000

# # ===============================
# # LOAD MODEL ONCE
# # ===============================
# model = SentenceTransformer("all-MiniLM-L6-v2")

# # ===============================
# # HELPERS
# # ===============================
# def extract_text_from_pdf(pdf_path):
#     texts = []
#     with pdfplumber.open(pdf_path) as pdf:
#         for page in pdf.pages[:MAX_PAGES]:
#             t = page.extract_text()
#             if t:
#                 texts.append(t)
#     return "\n".join(texts).lower()[:MAX_TEXT_CHARS]


# def embed(text: str):
#     return model.encode(
#         text[:MAX_TEXT_CHARS],
#         normalize_embeddings=True
#     )


# def similarity(vec_a, vec_b):
#     return float(cosine_similarity([vec_a], [vec_b])[0][0])

# # ===============================
# # REQUIREMENT EXTRACTION
# # ===============================
# def extract_experience_requirement(jd):
#     m = re.search(r"(\d+)\+?\s+years", jd)
#     return int(m.group(1)) if m else None


# def extract_project_requirement(jd):
#     return "project based development" if "project" in jd else None


# def extract_responsibility_requirements(jd):
#     keywords = ["design", "develop", "deploy", "optimize", "maintain", "collaborate", "lead", "scale"]
#     return [k for k in keywords if k in jd]


# def extract_domain(jd):
#     domains = ["finance", "healthcare", "ecommerce", "banking", "education", "ai", "ml"]
#     for d in domains:
#         if d in jd:
#             return d
#     return None

# # ===============================
# # GAP DETECTORS
# # ===============================
# def detect_experience_gap(resume, jd):
#     req = extract_experience_requirement(jd)
#     if not req:
#         return None

#     years = re.findall(r"(\d+)\s+years", resume)
#     resume_years = max(map(int, years)) if years else 0

#     if resume_years < req:
#         return f"JD requires {req}+ years, resume shows {resume_years}"
#     return None


# def detect_project_gap(resume_vec):
#     sim = similarity(embed("hands-on real world projects"), resume_vec)
#     return "JD expects strong project experience" if sim < 0.55 else None


# def detect_responsibility_gap(resume_vec, jd):
#     gaps = []
#     for r in extract_responsibility_requirements(jd):
#         sim = similarity(embed(f"experience to {r} systems"), resume_vec)
#         if sim < 0.50:
#             gaps.append(f"Missing responsibility: {r}")
#     return gaps or None


# def detect_domain_gap(resume_vec, jd):
#     domain = extract_domain(jd)
#     if not domain:
#         return None

#     sim = similarity(embed(f"{domain} domain experience"), resume_vec)
#     return f"No clear {domain} domain experience" if sim < 0.55 else None

# # ===============================
# # SKILL GAP (ALIAS + SEMANTIC)
# # ===============================
# SKILL_ALIASES = {
#     "rest api": ["rest api", "restful api", "apis"],
#     "react": ["react", "reactjs"],
#     "node": ["node", "nodejs"],
#     "mongodb": ["mongodb", "mongo"],
#     "express": ["express"],
#     "docker": ["docker", "container"],
#     "aws": ["aws", "ec2", "s3"]
# }

# def semantic_skill_gap(resume_text, resume_vec, jd):
#     missing = []
#     for skill, aliases in SKILL_ALIASES.items():
#         if skill in jd:
#             if any(a in resume_text for a in aliases):
#                 continue
#             sim = similarity(embed(f"experience with {skill}"), resume_vec)
#             if sim < 0.55:
#                 missing.append(skill)
#     return missing

# # ===============================
# # MAIN ANALYSIS
# # ===============================
# def full_gap_analysis(resume, jd):
#     resume_vec = embed(resume)
#     jd_vec = embed(jd)

#     score = similarity(resume_vec, jd_vec) * 100

#     verdict = (
#         "STRONG MATCH" if score >= 70 else
#         "MODERATE MATCH" if score >= 50 else
#         "WEAK MATCH"
#     )

#     return {
#         "semantic_match_score": round(score, 2),
#         "verdict": verdict,
#         "missing_skills": semantic_skill_gap(resume, resume_vec, jd),
#         "missing_experience": detect_experience_gap(resume, jd),
#         "missing_projects": detect_project_gap(resume_vec),
#         "missing_responsibilities": detect_responsibility_gap(resume_vec, jd),
#         "missing_domain": detect_domain_gap(resume_vec, jd)
#     }

# # ===============================
# # API
# # ===============================
# @router.post("/full-gap-analysis")
# async def analyze(
#     resume: UploadFile = File(...),
#     job_description: str = Form(...)
# ):
#     if not resume.filename.lower().endswith(".pdf"):
#         raise HTTPException(400, "Only PDF allowed")

#     with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
#         tmp.write(await resume.read())
#         path = tmp.name

#     try:
#         resume_text = extract_text_from_pdf(path)
#         if not resume_text:
#             raise HTTPException(400, "Unable to extract resume text")

#         result = full_gap_analysis(resume_text, job_description.lower())
#         return {"status": "success", **result}

#     finally:
#         os.remove(path)


from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import pdfplumber, tempfile, os, re
from functools import lru_cache
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

router = APIRouter(
    prefix="/semantic",
    tags=["Semantic Matching"]
)

# ===============================
# SAFETY LIMITS
# ===============================
MAX_PAGES = 4
MAX_TEXT_CHARS = 4000

# ===============================
# LOAD MODEL (LAZY + SAFE)
# ===============================
@lru_cache(maxsize=1)
def get_model():
    return SentenceTransformer("all-MiniLM-L6-v2")

# ===============================
# HELPERS
# ===============================
def extract_text_from_pdf(pdf_path: str) -> str:
    texts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages[:MAX_PAGES]:
            t = page.extract_text()
            if t:
                texts.append(t)

    return "\n".join(texts).lower()[:MAX_TEXT_CHARS]


def embed(text: str):
    model = get_model()
    return model.encode(
        text[:MAX_TEXT_CHARS],
        normalize_embeddings=True
    )


def similarity(vec_a, vec_b) -> float:
    return float(cosine_similarity([vec_a], [vec_b])[0][0])

# ===============================
# REQUIREMENT EXTRACTION
# ===============================
def extract_experience_requirement(jd: str):
    m = re.search(r"(\d+)\+?\s+years", jd)
    return int(m.group(1)) if m else None


def extract_responsibility_requirements(jd: str):
    keywords = [
        "design", "develop", "deploy",
        "optimize", "maintain", "collaborate",
        "lead", "scale"
    ]
    return [k for k in keywords if k in jd]


def extract_domain(jd: str):
    domains = ["finance", "healthcare", "ecommerce", "banking", "education", "ai", "ml"]
    for d in domains:
        if d in jd:
            return d
    return None

# ===============================
# GAP DETECTORS
# ===============================
def detect_experience_gap(resume: str, jd: str):
    req = extract_experience_requirement(jd)
    if not req:
        return None

    years = re.findall(r"(\d+)\s+years", resume)
    resume_years = max(map(int, years)) if years else 0

    if resume_years < req:
        return f"JD requires {req}+ years, resume shows {resume_years}"
    return None


def detect_project_gap(resume_vec):
    sim = similarity(embed("hands-on real world projects"), resume_vec)
    return "JD expects strong project experience" if sim < 0.55 else None


def detect_responsibility_gap(resume_vec, jd: str):
    gaps = []
    for r in extract_responsibility_requirements(jd):
        sim = similarity(embed(f"experience to {r} systems"), resume_vec)
        if sim < 0.50:
            gaps.append(f"Missing responsibility: {r}")
    return gaps or None


def detect_domain_gap(resume_vec, jd: str):
    domain = extract_domain(jd)
    if not domain:
        return None

    sim = similarity(embed(f"{domain} domain experience"), resume_vec)
    return f"No clear {domain} domain experience" if sim < 0.55 else None

# ===============================
# SKILL GAP (SEMANTIC)
# ===============================
SKILL_ALIASES = {
    "rest api": ["rest api", "restful api", "apis"],
    "react": ["react", "reactjs"],
    "node": ["node", "nodejs"],
    "mongodb": ["mongodb", "mongo"],
    "express": ["express"],
    "docker": ["docker", "container"],
    "aws": ["aws", "ec2", "s3"]
}


def semantic_skill_gap(resume_text: str, resume_vec, jd: str):
    missing = []
    for skill, aliases in SKILL_ALIASES.items():
        if skill in jd:
            if any(a in resume_text for a in aliases):
                continue

            sim = similarity(embed(f"experience with {skill}"), resume_vec)
            if sim < 0.55:
                missing.append(skill)

    return missing

# ===============================
# MAIN ANALYSIS
# ===============================
def full_gap_analysis(resume: str, jd: str):
    resume_vec = embed(resume)
    jd_vec = embed(jd)

    score = similarity(resume_vec, jd_vec) * 100

    verdict = (
        "STRONG MATCH" if score >= 70 else
        "MODERATE MATCH" if score >= 50 else
        "WEAK MATCH"
    )

    return {
        "semantic_match_score": round(score, 2),
        "verdict": verdict,
        "missing_skills": semantic_skill_gap(resume, resume_vec, jd),
        "missing_experience": detect_experience_gap(resume, jd),
        "missing_projects": detect_project_gap(resume_vec),
        "missing_responsibilities": detect_responsibility_gap(resume_vec, jd),
        "missing_domain": detect_domain_gap(resume_vec, jd)
    }

# ===============================
# API
# ===============================
@router.post("/full-gap-analysis")
async def analyze(
    resume: UploadFile = File(...),
    job_description: str = Form(...)
):
    if not resume.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF allowed")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await resume.read())
        path = tmp.name

    try:
        resume_text = extract_text_from_pdf(path)
        if not resume_text.strip():
            raise HTTPException(400, "Unable to extract resume text")

        result = full_gap_analysis(resume_text, job_description.lower())
        return {"status": "success", **result}

    finally:
        os.remove(path)
