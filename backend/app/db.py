"""MongoDB connection and initialization using Beanie ODM."""

from urllib.parse import urlparse

from motor.motor_asyncio import AsyncIOMotorClient

from beanie import init_beanie

from app.config import get_settings


async def init_db() -> None:
    """Initialize the MongoDB connection and Beanie ODM."""
    from app.models.user import User
    from app.models.project import ProjectDocument

    settings = get_settings()
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db]

    await init_beanie(
        database=db,
        document_models=[User, ProjectDocument],
    )

    parsed = urlparse(settings.mongodb_uri)
    # Show only host (no user/password): for mongodb+srv, netloc is user:pass@host
    netloc = parsed.netloc or ""
    host = netloc.split("@")[-1] if "@" in netloc else (parsed.hostname or netloc)
    print(f"Connected to MongoDB: {host}/{settings.mongodb_db}")
