"""MongoDB connection and initialization using Beanie ODM."""

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

    print(f"Connected to MongoDB: {settings.mongodb_uri}/{settings.mongodb_db}")
