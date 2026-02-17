"""Pipeline execution endpoints."""

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sse_starlette.sse import EventSourceResponse

from app.auth import get_current_user
from app.models.user import User
from app.schemas.projects import Project, ProjectCreate
from app.services import PipelineService

router = APIRouter()


@router.post("/run", response_model=Project)
async def run_pipeline(
    request: ProjectCreate,
    user: User = Depends(get_current_user),
) -> Project:
    """
    Create a project and run the complete agent pipeline.

    Requires authentication. Checks credit limits for free users.
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

    project = await service.run_pipeline(project.id, request.prompt)
    return project


@router.post("/stream")
async def stream_pipeline(
    request: ProjectCreate,
    user: User = Depends(get_current_user),
):
    """
    Create a project and stream the agent pipeline execution.

    Requires authentication. Checks credit limits for free users.
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

    async def event_generator():
        try:
            async for event in service.stream_pipeline(
                project.id,
                request.prompt,
            ):
                yield {
                    "event": event.get("type", "update"),
                    "data": json.dumps(event),
                }
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)}),
            }

    return EventSourceResponse(event_generator())


@router.post("/{project_id}/run", response_model=Project)
async def run_project_pipeline(
    project_id: str,
    user: User = Depends(get_current_user),
) -> Project:
    """
    Run the pipeline for an existing project.

    Does NOT consume credits (project already created).
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

    project = await service.run_pipeline(project_id, project.prompt)
    return project


@router.post("/{project_id}/stream")
async def stream_project_pipeline(
    project_id: str,
    user: User = Depends(get_current_user),
):
    """
    Stream pipeline execution for an existing project.

    Does NOT consume credits (project already created).
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

    async def event_generator():
        try:
            async for event in service.stream_pipeline(
                project_id,
                project.prompt,
            ):
                yield {
                    "event": event.get("type", "update"),
                    "data": json.dumps(event),
                }
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)}),
            }

    return EventSourceResponse(event_generator())


@router.get("/{project_id}/status")
async def get_pipeline_status(
    project_id: str,
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get the current pipeline status for a project.
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

    status_data = project.state.pipeline_status
    return {
        "project_id": project_id,
        "stage": status_data.stage if status_data else "unknown",
        "progress": status_data.progress if status_data else 0,
        "current_agent": status_data.current_agent if status_data else None,
        "message": status_data.message if status_data else "",
        "started_at": status_data.started_at.isoformat() if status_data and status_data.started_at else None,
        "completed_at": status_data.completed_at.isoformat() if status_data and status_data.completed_at else None,
    }


@router.get("/{project_id}/artifacts")
async def get_pipeline_artifacts(
    project_id: str,
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get all artifacts (agent outputs) from a pipeline execution.
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

    artifacts = {}

    if project.state.manager_output:
        artifacts["manager"] = project.state.manager_output.model_dump()

    if project.state.architect_output:
        artifacts["architect"] = project.state.architect_output.model_dump()

    if project.state.engineer_output:
        artifacts["engineer"] = project.state.engineer_output.model_dump()

    if project.state.qa_output:
        artifacts["qa"] = project.state.qa_output.model_dump()

    return {
        "project_id": project_id,
        "artifacts": artifacts,
    }
