from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta
import httpx

from app.core.database import get_db
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
)
from app.core.config import settings
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UserResponse,
    MessageResponse,
    GoogleAuthRequest,
    VerifyEmailRequest,
    ResendVerificationRequest,
)
from app.services.email_service import send_verification_email

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def _create_verification_token(user_id: str) -> str:
    """Create a short-lived JWT for email verification."""
    from app.core.security import create_access_token
    return create_access_token(
        {"sub": user_id, "purpose": "email_verify"},
        expires_delta=timedelta(hours=24),
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        full_name=req.full_name,
        email=req.email,
        password_hash=hash_password(req.password),
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Send verification email (non-blocking — won't crash if SMTP fails)
    try:
        token = _create_verification_token(str(user.user_id))
        send_verification_email(user.email, user.full_name, token)
    except Exception:
        pass  # Registration succeeds even if email fails

    return user


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(User.email == req.email, User.is_active == True)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    try:
        from app.services import gamification_service as _gs
        await _gs.on_login(db, user.user_id)
    except Exception:
        pass  # login must succeed regardless of gamification errors

    token_data = {"sub": str(user.user_id), "role": user.role}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(req: VerifyEmailRequest, db: AsyncSession = Depends(get_db)):
    """Verify a user's email using the token from the verification link."""
    try:
        payload = decode_token(req.token)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification link",
        )

    if payload.get("purpose") != "email_verify":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token",
        )

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.email_verified:
        return MessageResponse(message="Email already verified")

    user.email_verified = True
    await db.commit()
    return MessageResponse(message="Email verified successfully")


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification(req: ResendVerificationRequest, db: AsyncSession = Depends(get_db)):
    """Resend the verification email."""
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()

    if not user:
        # Don't reveal whether email exists
        return MessageResponse(message="If the email exists, a verification link has been sent")

    if user.email_verified:
        return MessageResponse(message="Email already verified")

    token = _create_verification_token(str(user.user_id))
    send_verification_email(user.email, user.full_name, token)
    return MessageResponse(message="If the email exists, a verification link has been sent")


@router.post("/google", response_model=TokenResponse)
async def google_auth(req: GoogleAuthRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate with Google. Creates account if user doesn't exist."""
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth is not configured",
        )

    # Verify the Google token with Google's API
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://oauth2.googleapis.com/tokeninfo?id_token={req.credential}"
        )

    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token",
        )

    google_data = resp.json()
    google_email = google_data.get("email")
    google_name = google_data.get("name", google_email.split("@")[0])
    aud = google_data.get("aud")

    # Verify the token was issued for our app
    if aud != settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google token was not issued for this application",
        )

    if not google_data.get("email_verified"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google email is not verified",
        )

    # Check if user exists
    result = await db.execute(select(User).where(User.email == google_email))
    user = result.scalar_one_or_none()

    if not user:
        # Create new user — no password needed (Google-authenticated)
        user = User(
            full_name=google_name,
            email=google_email,
            password_hash="GOOGLE_OAUTH_NO_PASSWORD",
            email_verified=True,
            avatar_url=google_data.get("picture"),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        # Existing user — mark email as verified if not already
        if not user.email_verified:
            user.email_verified = True
        if not user.avatar_url and google_data.get("picture"):
            user.avatar_url = google_data.get("picture")
        await db.commit()

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    token_data = {"sub": str(user.user_id), "role": user.role}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(req: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(req.refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = payload.get("sub")
    result = await db.execute(
        select(User).where(User.user_id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    token_data = {"sub": str(user.user_id), "role": user.role}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user