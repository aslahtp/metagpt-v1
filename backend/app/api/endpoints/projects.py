"""Project management endpoints."""

from typing import Any

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth import get_current_user
from app.models.user import User
from app.schemas.projects import Project, ProjectCreate
from app.services import PipelineService

router = APIRouter()


@router.post("", response_model=Project, status_code=status.HTTP_201_CREATED)
async def create_project(
    request: ProjectCreate,
    user: User = Depends(get_current_user),
) -> Project:
    """
    Create a new project from a natural language prompt.

    Requires authentication. Checks credit limits for free users.
    Premium users bypass credit checks.
    """
    if not user.has_credits():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"You've used all your free credits ({user.credits_used}/{user.credits_limit}). "
                "Upgrade to premium for unlimited projects."
            ),
        )

    service = PipelineService()
    project = await service.create_project(request.prompt, user_id=str(user.id))

    # Increment credits used
    user.credits_used += 1
    await user.save()

    return project


@router.get("", response_model=list[Project])
async def list_projects(
    limit: int = 50,
    offset: int = 0,
    user: User = Depends(get_current_user),
) -> list[Project]:
    """
    List projects for the current user.

    Returns projects sorted by most recently updated.
    """
    service = PipelineService()
    return await service.list_projects(limit, offset, user_id=str(user.id))


@router.get("/{project_id}", response_model=Project)
async def get_project(
    project_id: str,
    user: User = Depends(get_current_user),
) -> Project:
    """
    Get a project by ID.

    Returns the complete project state including all agent outputs.
    Only the project owner can access it.
    """
    service = PipelineService()
    project = await service.get_project(project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    if project.user_id != str(user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this project",
        )

    return project


@router.get("/{project_id}/state")
async def get_project_state(
    project_id: str,
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get the current state of a project.

    Returns agent outputs and pipeline status.
    """
    service = PipelineService()
    project = await service.get_project(project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    if project.user_id != str(user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this project",
        )

    return {
        "project_id": project.id,
        "name": project.name,
        "description": project.description,
        "pipeline_status": project.state.pipeline_status.model_dump() if project.state.pipeline_status else None,
        "preview": project.preview.model_dump() if project.preview else None,
        "has_manager_output": project.state.manager_output is not None,
        "has_architect_output": project.state.architect_output is not None,
        "has_engineer_output": project.state.engineer_output is not None,
        "has_qa_output": project.state.qa_output is not None,
    }


@router.get("/{project_id}/reasoning")
async def get_agent_reasoning(
    project_id: str,
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get the reasoning from all agents for a project.
    """
    service = PipelineService()
    project = await service.get_project(project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    if project.user_id != str(user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this project",
        )

    reasoning = {}

    if project.state.manager_output:
        reasoning["manager"] = {
            "agent": "ManagerAgent",
            "reasoning": project.state.manager_output.reasoning,
        }

    if project.state.architect_output:
        reasoning["architect"] = {
            "agent": "ArchitectAgent",
            "reasoning": project.state.architect_output.reasoning,
        }

    if project.state.engineer_output:
        reasoning["engineer"] = {
            "agent": "EngineerAgent",
            "reasoning": project.state.engineer_output.reasoning,
        }

    if project.state.qa_output:
        reasoning["qa"] = {
            "agent": "QAAgent",
            "reasoning": project.state.qa_output.reasoning,
        }

    return {
        "project_id": project_id,
        "reasoning": reasoning,
    }


@router.get("/{project_id}/preview")
async def get_preview_metadata(
    project_id: str,
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get preview metadata for a project.
    """
    service = PipelineService()
    project = await service.get_project(project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    if project.user_id != str(user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this project",
        )

    return {
        "project_id": project_id,
        "preview": project.preview.model_dump() if project.preview else None,
    }


@router.post("/{project_id}/index")
async def index_project_files(
    project_id: str,
    request: dict[str, list[str]] | None = None,  # Accept raw dict or use Pydantic
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Trigger re-indexing for specific files or the entire project.
    """
    # Extract files from body if present
    files = request.get("files") if request else None

    service = PipelineService()
    project = await service.get_project(project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    if project.user_id != str(user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this project",
        )

    # Lazy import to avoid circular dependencies if any
    from app.rag.indexer import CodebaseIndexer
    indexer = CodebaseIndexer()

    try:
        if files:
            await indexer.reindex_files(project_id, files)
            return {"status": "completed", "files_indexed": len(files)}
        else:
            stats = await indexer.index_project(project_id)
            return {"status": "completed", "stats": stats}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Indexing failed: {str(e)}",
        )
