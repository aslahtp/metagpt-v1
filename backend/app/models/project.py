"""Project document model for MongoDB."""

from datetime import datetime
from typing import Any

from beanie import Document
from pydantic import Field
from pymongo import IndexModel

from app.schemas.agents import (
    ArchitectOutput,
    EngineerOutput,
    ManagerOutput,
    QAOutput,
)
from app.schemas.projects import (
    PipelineStage,
    PipelineStatus,
    PreviewMetadata,
    ProjectState,
)


class ProjectDocument(Document):
    """Project document stored in MongoDB."""

    project_id: str = Field(..., description="Short project identifier")
    user_id: str = Field(..., description="Owner user ID")
    prompt: str = Field(..., description="Original user prompt")
    name: str = Field(default="", description="Project name (set by Manager)")
    description: str = Field(default="", description="Project description")
    state: ProjectState = Field(default_factory=ProjectState)
    preview: PreviewMetadata = Field(default_factory=PreviewMetadata)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = Field(default=1, description="Project version for iterations")

    class Settings:
        name = "projects"
        indexes = [
            IndexModel([("project_id", 1)], unique=True),
            IndexModel([("user_id", 1)]),
        ]

    def to_api_model(self) -> dict[str, Any]:
        """Convert to the API response format matching the Project schema."""
        return {
            "id": self.project_id,
            "user_id": self.user_id,
            "prompt": self.prompt,
            "name": self.name,
            "description": self.description,
            "state": self.state.model_dump(mode="json"),
            "preview": self.preview.model_dump(mode="json"),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
        }
