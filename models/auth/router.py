from fastapi import APIRouter, HTTPException, status
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
@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(data: SignupSchema):
    if users_collection.find_one({"email": data.email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )

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

    if not user or not verify_password(data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    token = create_access_token({"sub": user["email"]})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "name": user["name"],
            "email": user["email"]
        }
    }
