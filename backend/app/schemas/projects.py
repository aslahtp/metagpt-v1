"""Schemas for project management."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.agents import (
    ArchitectOutput,
    EngineerOutput,
    ManagerOutput,
    QAOutput,
)


class PipelineStage(str, Enum):
    """Pipeline execution stages."""

    PENDING = "pending"
    MANAGER = "manager"
    ARCHITECT = "architect"
    ENGINEER = "engineer"
    QA = "qa"
    COMPLETED = "completed"
    ERROR = "error"


class PipelineStatus(BaseModel):
    """Current status of the pipeline execution."""

    stage: PipelineStage = Field(..., description="Current stage")
    progress: float = Field(..., ge=0, le=100, description="Progress percentage")
    current_agent: str | None = Field(None, description="Currently executing agent")
    message: str = Field(default="", description="Status message")
    started_at: datetime | None = Field(None, description="When execution started")
    completed_at: datetime | None = Field(None, description="When execution completed")


class ProjectCreate(BaseModel):
    """Request to create a new project."""

    prompt: str = Field(..., min_length=10, description="Natural language project prompt")
    options: dict[str, Any] = Field(
        default_factory=dict, description="Optional configuration"
    )


class ProjectState(BaseModel):
    """Complete state of a project including all agent outputs."""

    manager_output: ManagerOutput | None = None
    architect_output: ArchitectOutput | None = None
    engineer_output: EngineerOutput | None = None
    qa_output: QAOutput | None = None
    pipeline_status: PipelineStatus = Field(
        default_factory=lambda: PipelineStatus(
            stage=PipelineStage.PENDING, progress=0
        )
    )


class PreviewMetadata(BaseModel):
    """Metadata for project preview capabilities."""

    is_react_project: bool = Field(False, description="Whether this is a React project")
    is_nextjs_project: bool = Field(False, description="Whether this is a Next.js project")
    entry_file: str | None = Field(None, description="Main entry file for preview")
    preview_supported: bool = Field(False, description="Whether preview is supported")
    framework: str | None = Field(None, description="Detected framework")


class Project(BaseModel):
    """Complete project representation."""

    id: str = Field(..., description="Unique project identifier")
    user_id: str = Field(default="", description="Owner user ID")
    prompt: str = Field(..., description="Original user prompt")
    name: str = Field(default="", description="Project name (set by Manager)")
    description: str = Field(default="", description="Project description")
    state: ProjectState = Field(default_factory=ProjectState)
    preview: PreviewMetadata = Field(default_factory=PreviewMetadata)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = Field(default=1, description="Project version for iterations")


class ChatMessage(BaseModel):
    """A message in the project chat."""

    id: str = Field(..., description="Message identifier")
    role: str = Field(..., description="Role: user or assistant")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agent_triggered: str | None = Field(None, description="Which agent was triggered")
    files_modified: list[str] = Field(
        default_factory=list, description="Files modified by this message"
    )


class ChatRequest(BaseModel):
    """Request to send a chat message."""

    message: str = Field(..., min_length=1, description="User message")
    context: dict[str, Any] = Field(
        default_factory=dict, description="Additional context"
    )
    model: str | None = Field(
        default=None,
        description="LLM model override (e.g. 'gemini-2.5-flash', 'gemini-2.5-pro'). None means auto.",
    )


class ChatResponse(BaseModel):
    """Response from chat processing."""

    message: ChatMessage = Field(..., description="Assistant response")
    agents_executed: list[str] = Field(
        default_factory=list, description="Agents that were executed"
    )
    files_modified: list[str] = Field(
        default_factory=list, description="Files that were modified"
    )
    files_referenced: list[str] = Field(
        default_factory=list, description="Files referenced via RAG context"
    )
    project_updated: bool = Field(False, description="Whether project state changed")
    indexing_status: str | None = Field(
        None, description="Status of RAG re-indexing (e.g. 'completed', 'failed')"
    )

