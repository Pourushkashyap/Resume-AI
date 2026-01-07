import pandas as pd
import numpy as np
import re
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

from models.model.resume_quality_score import compute_resume_quality_score

DATA_PATH = "./models/archive/Resume/Resume.csv"

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

    return [
        resume_length,
        num_skills,
        num_projects,
        num_bullets,
        experience_years,
        grammar_issues
    ]

print("📄 Loading resume dataset...")
df = pd.read_csv(DATA_PATH)
df = df[["Resume_str"]].dropna()

X, y = [], []

for resume_text in df["Resume_str"].astype(str):
    resume_text = resume_text[:6000]  # memory safety
    features = extract_features(resume_text)
    rule_score = compute_resume_quality_score(resume_text)["resume_score"]

    X.append(features)
    y.append(rule_score)

X = np.array(X)
y = np.array(y)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print("🤖 Training Resume Score ML model...")

model = RandomForestRegressor(
    n_estimators=300,
    max_depth=10,
    min_samples_split=5,
    min_samples_leaf=3,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)

predictions = model.predict(X_test)
mae = mean_absolute_error(y_test, predictions)

print(f"📉 MAE: {mae:.2f}")

MODEL_PATH = "./models/resume_score_model.pkl"
joblib.dump(model, MODEL_PATH)

print(f"💾 Model saved at: {MODEL_PATH}")
