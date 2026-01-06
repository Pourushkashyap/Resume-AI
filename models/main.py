from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models.auth.router import router as auth_router
from models.model.semantic_resume_jb_matcher import router as semantic_router
from models.model.resume_quality_score import router as quality_router
from models.model.resume_improvement_engine import router as improvement_router
from models.model.resume_ml_score import router as ml_score_router

app = FastAPI(title="AI Resume ATS System")

# ✅ CORS FIX
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(semantic_router)
app.include_router(quality_router)
app.include_router(improvement_router)
app.include_router(ml_score_router)
app.include_router(auth_router)

@app.get("/")
def root():
    return {"status": "ATS Backend Running"}
