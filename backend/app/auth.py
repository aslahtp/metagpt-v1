"""Authentication utilities: JWT tokens, password hashing, and FastAPI dependency."""

from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings
from app.models.user import User

# Use argon2 for password hashing (more secure and no compatibility issues)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
security = HTTPBearer()


def hash_password(password: str) -> str:
    """Hash a plaintext password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: str, email: str) -> str:
    """Create a JWT access token for a user."""
    settings = get_settings()
    expire = datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)
    payload = {
        "sub": user_id,
        "email": email,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> User:
    """
    FastAPI dependency that extracts and validates the JWT token,
    then returns the corresponding User document from MongoDB.
    """
    settings = get_settings()
    token = credentials.credentials

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    from beanie import PydanticObjectId

    try:
        user = await User.get(PydanticObjectId(user_id))
    except Exception:
        raise credentials_exception

    if user is None:
        raise credentials_exception

    return user
