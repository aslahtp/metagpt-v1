"""Project management endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.schemas.projects import Project, ProjectCreate
from app.services import PipelineService

router = APIRouter()


@router.post("", response_model=Project, status_code=status.HTTP_201_CREATED)
async def create_project(request: ProjectCreate) -> Project:
    """
    Create a new project from a natural language prompt.

    This creates the project record but does NOT execute the pipeline.
    Use POST /pipeline/{project_id}/run to execute the agent pipeline.
    """
    service = PipelineService()
    project = await service.create_project(request.prompt)
    return project


@router.get("", response_model=list[Project])
async def list_projects(
    limit: int = 50,
    offset: int = 0,
) -> list[Project]:
    """
    List all projects.

    Returns projects sorted by most recently updated.
    """
    service = PipelineService()
    return await service.list_projects(limit, offset)


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: str) -> Project:
    """
    Get a project by ID.

    Returns the complete project state including all agent outputs.
    """
    service = PipelineService()
    project = await service.get_project(project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    return project


@router.get("/{project_id}/state")
async def get_project_state(project_id: str) -> dict[str, Any]:
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
async def get_agent_reasoning(project_id: str) -> dict[str, Any]:
    """
    Get the reasoning from all agents for a project.

    Useful for understanding how agents made their decisions.
    """
    service = PipelineService()
    project = await service.get_project(project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
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
async def get_preview_metadata(project_id: str) -> dict[str, Any]:
    """
    Get preview metadata for a project.

    Indicates whether the project supports React preview.
    """
    service = PipelineService()
    project = await service.get_project(project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    return {
        "project_id": project_id,
        "preview": project.preview.model_dump() if project.preview else None,
    }
