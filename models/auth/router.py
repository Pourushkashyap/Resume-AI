from fastapi import APIRouter, HTTPException
from models.auth.schemas import SignupSchema, LoginSchema
from models.auth.utils import (
    users_collection,
    hash_password,
    verify_password,
    create_access_token
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# ---------------- SIGNUP ----------------
@router.post("/signup")
def signup(data: SignupSchema):
    if users_collection.find_one({"email": data.email}):
        raise HTTPException(400, "User already exists")

    users_collection.insert_one({
        "name": data.name,
        "email": data.email,
        "hashed_password": hash_password(data.password)
    })

    return {"message": "Signup successful"}

# ---------------- LOGIN ----------------
@router.post("/login")
def login(data: LoginSchema):
    user = users_collection.find_one({"email": data.email})
    if not user:
        raise HTTPException(401, "Invalid email or password")

    if not verify_password(data.password, user["hashed_password"]):
        raise HTTPException(401, "Invalid email or password")

    token = create_access_token({"sub": user["email"]})

    return {
        "access_token": token,
        "user": {
            "name": user["name"],
            "email": user["email"]
        }
    }
