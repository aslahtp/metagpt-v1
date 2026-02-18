"""Sandbox management endpoints for E2B preview."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user
from app.models.user import User
from app.services import PipelineService
from app.services.sandbox_service import SandboxService

router = APIRouter()

# Shared service instance (keeps in-memory sandbox registry)
_sandbox_service = SandboxService()


async def _get_project_for_user(project_id: str, user: User):
    """Helper to fetch a project and verify ownership."""
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

    return project, service


@router.post("/{project_id}/create")
async def create_sandbox(
    project_id: str,
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Create an E2B sandbox for live preview.

    Writes all generated project files into the sandbox,
    installs dependencies, starts the dev server, and returns
    the public preview URL.
    """
    project, service = await _get_project_for_user(project_id, user)

    if not project.state.engineer_output:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No generated code available — run the pipeline first.",
        )

    if not project.preview.preview_supported:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This project type does not support live preview.",
        )

    # Build the file list from engineer output
    files = [
        {"file_path": f.file_path, "file_content": f.file_content}
        for f in project.state.engineer_output.files
    ]

    try:
        info = await _sandbox_service.create_sandbox(project_id, files)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create sandbox: {e}",
        )

    return {
        "sandbox_id": info.sandbox_id,
        "preview_url": info.preview_url,
    }


@router.get("/{project_id}/status")
async def get_sandbox_status(
    project_id: str,
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Check if a sandbox is alive for the given project.
    """
    await _get_project_for_user(project_id, user)

    info = await _sandbox_service.get_sandbox_status(project_id)

    if not info:
        return {
            "alive": False,
            "sandbox_id": None,
            "preview_url": None,
        }

    return {
        "alive": True,
        "sandbox_id": info.sandbox_id,
        "preview_url": info.preview_url,
    }


@router.post("/{project_id}/kill")
async def kill_sandbox(
    project_id: str,
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Kill the sandbox for a project.
    """
    await _get_project_for_user(project_id, user)

    killed = await _sandbox_service.kill_sandbox(project_id)

    return {
        "killed": killed,
    }
