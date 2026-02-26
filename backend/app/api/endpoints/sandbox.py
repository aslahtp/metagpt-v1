"""Sandbox management endpoints for E2B preview.

/create   — non-blocking; returns 202 immediately and starts a background task.
/status   — poll this until status == "ready" (or "error").
/kill     — stop and destroy the sandbox.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user
from app.models.user import User
from app.services import PipelineService
from app.services.sandbox_service import SandboxService, SandboxStatus

router = APIRouter()

# Shared service instance (keeps in-memory sandbox registry and background tasks)
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


@router.post("/{project_id}/create", status_code=status.HTTP_202_ACCEPTED)
async def create_sandbox(
    project_id: str,
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Kick off E2B sandbox creation in the background.

    Returns **202 Accepted** immediately — the sandbox is NOT yet ready.
    Poll ``GET /{project_id}/status`` until ``status == "ready"`` (or ``"error"``).

    The full create flow (file writes + npm install + dev server) takes 60–120 s,
    which exceeds Cloud Run's HTTP request deadline, so we never block on it.
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

    files = [
        {"file_path": f.file_path, "file_content": f.file_content}
        for f in project.state.engineer_output.files
    ]

    info = _sandbox_service.start_sandbox_creation(project_id, files)

    return {
        "status": info.status,
        "sandbox_id": info.sandbox_id,
        "preview_url": info.preview_url,
        "message": "Sandbox creation started. Poll /status for progress.",
    }


@router.get("/{project_id}/status")
async def get_sandbox_status(
    project_id: str,
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Poll the sandbox build status for a project.

    Possible ``status`` values:
    - ``"pending"``  — queued, not yet started
    - ``"building"`` — installing deps / starting dev server
    - ``"ready"``    — preview_url is live
    - ``"error"``    — build failed; see ``error_message``
    - ``null``       — no sandbox found for this project (``alive: false``)
    """
    await _get_project_for_user(project_id, user)

    info = await _sandbox_service.get_sandbox_status(project_id)

    if not info:
        return {
            "alive": False,
            "status": None,
            "sandbox_id": None,
            "preview_url": None,
            "error_message": None,
        }

    return {
        "alive": info.status == SandboxStatus.READY,
        "status": info.status,
        "sandbox_id": info.sandbox_id,
        "preview_url": info.preview_url,
        "error_message": info.error_message,
        "logs": info.logs,
    }


@router.post("/{project_id}/kill")
async def kill_sandbox(
    project_id: str,
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Kill the sandbox for a project (also cancels any in-progress build).
    """
    await _get_project_for_user(project_id, user)

    killed = await _sandbox_service.kill_sandbox(project_id)

    return {"killed": killed}
