from fastapi import FastAPI, UploadFile, File, Form, HTTPException
import pdfplumber
import tempfile
import os

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from fastapi import Depends
from auth.dependencies import get_current_user



app = FastAPI(title="Semantic ATS Matcher (Model 6)")



semantic_model = SentenceTransformer("all-MiniLM-L6-v2")



def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()



def semantic_resume_jd_match(resume_text: str, jd_text: str):
    resume_embedding = semantic_model.encode(resume_text)
    jd_embedding = semantic_model.encode(jd_text)

    similarity = cosine_similarity(
        [resume_embedding], [jd_embedding]
    )[0][0]

    score = round(similarity * 100, 2)

    if score >= 75:
        verdict = "STRONG MATCH"
    elif score >= 50:
        verdict = "MODERATE MATCH"
    else:
        verdict = "WEAK MATCH"

    return {
        "semantic_match_score": score,
        "verdict": verdict
    }



@app.post("/semantic-match")
async def semantic_match_api(
     resume: UploadFile = File(...),
     job_description: str = Form(...),
     current_user: str = Depends(get_current_user)
):
    # Validate file
    if not resume.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF resumes allowed")

    # Save PDF temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await resume.read())
        tmp_path = tmp.name

    try:
        # Extract resume text
        resume_text = extract_text_from_pdf(tmp_path)

        if not resume_text:
            raise HTTPException(status_code=400, detail="Could not extract resume text")

        # Semantic match
        result = semantic_resume_jd_match(resume_text, job_description)

        return {
            "status": "success",
            "semantic_match_score": result["semantic_match_score"],
            "verdict": result["verdict"]
        }

    finally:
        os.remove(tmp_path)
