"""User document model for MongoDB."""

from datetime import datetime

from beanie import Document
from pydantic import EmailStr, Field
from pymongo import IndexModel


class User(Document):
    """User document stored in MongoDB."""

    email: str = Field(..., description="User email address")
    password_hash: str = Field(..., description="Hashed password")
    name: str = Field(default="", description="Display name")
    is_premium_user: bool = Field(default=False, description="Premium status bypasses credit limits")
    credits_used: int = Field(default=0, description="Number of projects created")
    credits_limit: int = Field(default=2, description="Maximum free projects allowed")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"
        indexes = [
            IndexModel([("email", 1)], unique=True),
        ]

    def has_credits(self) -> bool:
        """Check if user can create a new project."""
        if self.is_premium_user:
            return True
        return self.credits_used < self.credits_limit

    def remaining_credits(self) -> int | None:
        """Return remaining credits, or None if premium (unlimited)."""
        if self.is_premium_user:
            return None
        return max(0, self.credits_limit - self.credits_used)
