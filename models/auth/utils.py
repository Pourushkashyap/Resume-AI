from pymongo import MongoClient
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# ---------------- LOAD ENV ----------------
# utils.py -> auth -> models
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_PATH)

SECRET_KEY = os.getenv("SECRET_KEY")
MONGO_URI = os.getenv("MONGO_URI")

print("ENV PATH =", ENV_PATH)
print("SECRET_KEY =", SECRET_KEY)
print("MONGO_URI =", MONGO_URI)

if not SECRET_KEY:
    raise ValueError("SECRET_KEY not found in .env")

if not MONGO_URI:
    raise ValueError("MONGO_URI not found in .env")

# ---------------- CONFIG ----------------
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------------- DB ----------------
client = MongoClient(MONGO_URI)
db = client["resume_ai"]
users_collection = db["users"]

# ---------------- PASSWORD ----------------
def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str):
    return pwd_context.verify(password, hashed)

# ---------------- JWT ----------------
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
