from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime


class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    user_id: UUID
    full_name: str
    email: str
    role: str
    is_active: bool
    email_verified: bool
    avatar_url: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    message: str


class GoogleAuthRequest(BaseModel):
    credential: str


class VerifyEmailRequest(BaseModel):
    token: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr
