from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from storage.user_store import create_user, get_user_by_email
from api.auth import hash_password, verify_password, create_access_token

router = APIRouter()

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str  # min 8 chars enforced on FE

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str

@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest):
    if get_user_by_email(req.email):
        raise HTTPException(400, "Email already registered.")
    if len(req.password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters.")
    
    hashed = hash_password(req.password)
    user = create_user(req.email, hashed)
    token = create_access_token(user["id"])
    return TokenResponse(access_token=token, user_id=user["id"], email=user["email"])

@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest):
    user = get_user_by_email(req.email)
    if not user or not verify_password(req.password, user["hashed_password"]):
        raise HTTPException(401, "Invalid email or password.")
    token = create_access_token(user["id"])
    return TokenResponse(access_token=token, user_id=user["id"], email=user["email"])
