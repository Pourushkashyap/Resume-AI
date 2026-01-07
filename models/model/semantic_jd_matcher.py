from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
import pdfplumber
import tempfile
import os
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from models.auth.dependencies import get_current_user

app = FastAPI(title="Semantic ATS Matcher (Model 6)")

# =================================================
# LIMITS (VERY IMPORTANT FOR RENDER)
# =================================================
MAX_PAGES = 4
MAX_TEXT_CHARS = 4000   # transformer safe limit

# =================================================
# LOAD MODEL ONCE
# =================================================
semantic_model = SentenceTransformer("all-MiniLM-L6-v2")

# =================================================
# UTILS
# =================================================
def extract_text_from_pdf(pdf_path: str) -> str:
    texts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages[:MAX_PAGES]:
            t = page.extract_text()
            if t:
                texts.append(t)

    text = "\n".join(texts)
    return text[:MAX_TEXT_CHARS].strip()


def semantic_resume_jd_match(resume_text: str, jd_text: str):
    # truncate JD also (very important)
    resume_text = resume_text[:MAX_TEXT_CHARS]
    jd_text = jd_text[:MAX_TEXT_CHARS]

    resume_embedding = semantic_model.encode(
        resume_text, normalize_embeddings=True
    )
    jd_embedding = semantic_model.encode(
        jd_text, normalize_embeddings=True
    )

    similarity = cosine_similarity(
        [resume_embedding], [jd_embedding]
    )[0][0]

    score = round(similarity * 100, 2)

    verdict = (
        "STRONG MATCH" if score >= 75
        else "MODERATE MATCH" if score >= 50
        else "WEAK MATCH"
    )

    return {
        "semantic_match_score": score,
        "verdict": verdict
    }

# =================================================
# API
# =================================================
@app.post("/semantic-match")
async def semantic_match_api(
    resume: UploadFile = File(...),
    job_description: str = Form(...),
    current_user: str = Depends(get_current_user)
):
    if not resume.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF resumes allowed")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await resume.read())
        path = tmp.name

    try:
        resume_text = extract_text_from_pdf(path)

        if not resume_text:
            raise HTTPException(400, "Could not extract resume text")

        result = semantic_resume_jd_match(resume_text, job_description)

        return {
            "status": "success",
            "semantic_match_score": result["semantic_match_score"],
            "verdict": result["verdict"]
        }

    finally:
        os.remove(path)
