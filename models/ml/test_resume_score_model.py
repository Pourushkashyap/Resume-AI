import joblib
from ml.train_resume_score_model import extract_features
from model.resume_quality_score import compute_resume_quality_score

model = joblib.load("models/resume_score_model.pkl")


with open("models/sample_resume.txt", "r", encoding="utf-8") as f:
    resume_text = f.read()


features = extract_features(resume_text)
ml_score = model.predict([features])[0]
rule_score = compute_resume_quality_score(resume_text)["resume_score"]

print("Rule-based Score:", rule_score)
print("ML Predicted Score:", round(ml_score, 2))


bad_resume = "I worked on many things. Basic knowledge."

features = extract_features(bad_resume)
print(model.predict([features])[0])


good_resume = """
Software Engineer with 3 years of experience.

Skills: React, Node.js, MongoDB, AWS, Docker

Projects:
• Built scalable MERN application serving 10k users
• Optimized API performance by 40%
"""

features = extract_features(good_resume)
print(model.predict([features])[0])