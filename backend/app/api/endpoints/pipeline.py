"""Pipeline execution endpoints."""

import json
from typing import Any

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from app.schemas.projects import Project, ProjectCreate
from app.services import PipelineService

router = APIRouter()


@router.post("/run", response_model=Project)
async def run_pipeline(request: ProjectCreate) -> Project:
    """
    Create a project and run the complete agent pipeline.

    This is the main entry point for generating a project from a prompt.
    Executes: Manager → Architect → Engineer → QA

    Returns the complete project with all agent outputs.
    Note: This is a synchronous call that waits for pipeline completion.
    For streaming updates, use POST /pipeline/stream instead.
    """
    service = PipelineService()
    project = await service.create_project(request.prompt)
    project = await service.run_pipeline(project.id, request.prompt)
    return project


@router.post("/stream")
async def stream_pipeline(request: ProjectCreate):
    """
    Create a project and stream the agent pipeline execution.

    Returns a Server-Sent Events (SSE) stream with real-time updates
    as each agent completes.

    Event types:
    - pipeline_start: Pipeline execution started
    - agent_complete: An agent has completed
    - file_generated: A file was generated
    - pipeline_complete: Pipeline finished successfully
    - pipeline_error: An error occurred
    """
    service = PipelineService()
    project = await service.create_project(request.prompt)

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
async def run_project_pipeline(project_id: str) -> Project:
    """
    Run the pipeline for an existing project.

    Use this to (re-)run the pipeline for a project that was created
    but not yet executed, or to regenerate a project.
    """
    service = PipelineService()
    project = await service.get_project(project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    project = await service.run_pipeline(project_id, project.prompt)
    return project


@router.post("/{project_id}/stream")
async def stream_project_pipeline(project_id: str):
    """
    Stream pipeline execution for an existing project.

    Similar to POST /pipeline/stream but for an existing project.
    """
    service = PipelineService()
    project = await service.get_project(project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
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
async def get_pipeline_status(project_id: str) -> dict[str, Any]:
    """
    Get the current pipeline status for a project.

    Returns the current stage, progress, and any error information.
    """
    service = PipelineService()
    project = await service.get_project(project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
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
async def get_pipeline_artifacts(project_id: str) -> dict[str, Any]:
    """
    Get all artifacts (agent outputs) from a pipeline execution.

    Returns the complete output from each agent.
    """
    service = PipelineService()
    project = await service.get_project(project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
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
