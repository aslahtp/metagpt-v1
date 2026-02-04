"""File management endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.schemas.files import FileTree, GeneratedFile
from app.services import PipelineService

router = APIRouter()


class FileUpdateRequest(BaseModel):
    """Request to update a file's content."""
    content: str


@router.get("/{project_id}/tree", response_model=FileTree)
async def get_file_tree(project_id: str) -> FileTree:
    """
    Get the file tree for a project.

    Returns a hierarchical view of all generated files.
    """
    service = PipelineService()
    project = await service.get_project(project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    file_tree = await service.get_file_tree(project_id)

    if not file_tree:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No files found for project {project_id}",
        )

    return file_tree


@router.get("/{project_id}/list")
async def list_files(project_id: str) -> dict[str, Any]:
    """
    List all files in a project.

    Returns a flat list of file paths.
    """
    service = PipelineService()
    project = await service.get_project(project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    from app.storage import FileStore
    file_store = FileStore()
    files = await file_store.list_files(project_id)

    return {
        "project_id": project_id,
        "files": files,
        "total": len(files),
    }


@router.get("/{project_id}/content/{file_path:path}", response_model=GeneratedFile)
async def get_file_content(project_id: str, file_path: str) -> GeneratedFile:
    """
    Get the content of a specific file.

    Args:
        project_id: Project identifier
        file_path: Path to the file within the project
    """
    service = PipelineService()
    project = await service.get_project(project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    file = await service.get_file(project_id, file_path)

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File {file_path} not found in project {project_id}",
        )

    return file


@router.put("/{project_id}/content/{file_path:path}")
async def update_file_content(
    project_id: str,
    file_path: str,
    request: FileUpdateRequest,
) -> dict[str, Any]:
    """
    Update the content of a specific file.

    This allows direct file editing without going through agents.
    """
    service = PipelineService()
    project = await service.get_project(project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    from app.storage import FileStore
    file_store = FileStore()

    metadata = await file_store.update_file(project_id, file_path, request.content)

    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File {file_path} not found in project {project_id}",
        )

    return {
        "success": True,
        "file_path": file_path,
        "metadata": metadata.model_dump(),
    }


@router.delete("/{project_id}/content/{file_path:path}")
async def delete_file(project_id: str, file_path: str) -> dict[str, Any]:
    """
    Delete a file from the project.
    """
    service = PipelineService()
    project = await service.get_project(project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    from app.storage import FileStore
    file_store = FileStore()

    deleted = await file_store.delete_file(project_id, file_path)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File {file_path} not found in project {project_id}",
        )

    return {
        "success": True,
        "deleted": file_path,
    }


@router.get("/{project_id}/generated")
async def get_generated_files_summary(project_id: str) -> dict[str, Any]:
    """
    Get a summary of generated files from the Engineer agent.

    Returns file information without full content.
    """
    service = PipelineService()
    project = await service.get_project(project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    if not project.state.engineer_output:
        return {
            "project_id": project_id,
            "files": [],
            "total": 0,
        }

    files_summary = [
        {
            "path": f.file_path,
            "language": f.file_language,
            "purpose": f.file_purpose,
            "size": len(f.file_content),
        }
        for f in project.state.engineer_output.files
    ]

    return {
        "project_id": project_id,
        "files": files_summary,
        "total": len(files_summary),
    }
