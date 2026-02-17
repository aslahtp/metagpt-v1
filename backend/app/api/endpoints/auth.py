"""Authentication endpoints: signup, signin, and current user."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.config import get_settings
from app.models.user import User

router = APIRouter()


class SignUpRequest(BaseModel):
    """Request body for user registration."""

    email: str = Field(..., description="Email address")
    password: str = Field(..., min_length=6, description="Password (min 6 chars)")
    name: str = Field(default="", description="Display name")


class SignInRequest(BaseModel):
    """Request body for user login."""

    email: str = Field(..., description="Email address")
    password: str = Field(..., description="Password")


class AuthResponse(BaseModel):
    """Response returned after successful authentication."""

    token: str = Field(..., description="JWT access token")
    user: dict = Field(..., description="User profile data")


class UserProfile(BaseModel):
    """Public user profile information."""

    id: str
    email: str
    name: str
    is_premium_user: bool
    credits_used: int
    credits_limit: int
    remaining_credits: int | None
    created_at: str


def _user_profile(user: User) -> dict:
    """Build a user profile dict from a User document."""
    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "is_premium_user": user.is_premium_user,
        "credits_used": user.credits_used,
        "credits_limit": user.credits_limit,
        "remaining_credits": user.remaining_credits(),
        "created_at": user.created_at.isoformat(),
    }


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignUpRequest) -> AuthResponse:
    """
    Register a new user account.

    Creates a user with the configured number of free credits.
    Returns a JWT token and user profile.
    """
    settings = get_settings()

    existing = await User.find_one(User.email == request.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    user = User(
        email=request.email.lower().strip(),
        password_hash=hash_password(request.password),
        name=request.name.strip(),
        is_premium_user=False,
        credits_used=0,
        credits_limit=settings.free_credits,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    await user.insert()

    token = create_access_token(str(user.id), user.email)

    return AuthResponse(token=token, user=_user_profile(user))


@router.post("/signin", response_model=AuthResponse)
async def signin(request: SignInRequest) -> AuthResponse:
    """
    Authenticate an existing user.

    Validates email and password, returns a JWT token and user profile.
    """
    user = await User.find_one(User.email == request.email.lower().strip())
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(str(user.id), user.email)

    return AuthResponse(token=token, user=_user_profile(user))


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)) -> dict:
    """
    Get the current authenticated user's profile.

    Returns user info including credit usage and premium status.
    """
    return _user_profile(user)
