"""File management endpoints."""

import io
import zipfile
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.auth import get_current_user
from app.models.user import User
from app.schemas.files import FileTree, GeneratedFile
from app.services import PipelineService

router = APIRouter()


class FileUpdateRequest(BaseModel):
    """Request to update a file's content."""
    content: str


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


@router.get("/{project_id}/tree", response_model=FileTree)
async def get_file_tree(
    project_id: str,
    user: User = Depends(get_current_user),
) -> FileTree:
    """
    Get the file tree for a project.
    """
    project, service = await _get_project_for_user(project_id, user)

    file_tree = await service.get_file_tree(project_id)

    if not file_tree:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No files found for project {project_id}",
        )

    return file_tree


@router.get("/{project_id}/list")
async def list_files(
    project_id: str,
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    List all files in a project.
    """
    project, service = await _get_project_for_user(project_id, user)

    from app.storage import FileStore
    file_store = FileStore()
    files = await file_store.list_files(project_id)

    return {
        "project_id": project_id,
        "files": files,
        "total": len(files),
    }


@router.get("/{project_id}/content/{file_path:path}", response_model=GeneratedFile)
async def get_file_content(
    project_id: str,
    file_path: str,
    user: User = Depends(get_current_user),
) -> GeneratedFile:
    """
    Get the content of a specific file.
    """
    project, service = await _get_project_for_user(project_id, user)

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
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Update the content of a specific file.
    """
    project, service = await _get_project_for_user(project_id, user)

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
async def delete_file(
    project_id: str,
    file_path: str,
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Delete a file from the project.
    """
    project, service = await _get_project_for_user(project_id, user)

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


@router.get("/{project_id}/download")
async def download_project_zip(
    project_id: str,
    user: User = Depends(get_current_user),
) -> StreamingResponse:
    """
    Download all project files as a zip archive.
    """
    project, service = await _get_project_for_user(project_id, user)

    from app.storage import FileStore
    file_store = FileStore()

    files_dir = file_store._get_project_files_dir(project_id)

    if not files_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No files found for project {project_id}",
        )

    archive_name = (project.name or project_id).strip()
    archive_name = "".join(
        c if c.isalnum() or c in ("-", "_", " ") else "_" for c in archive_name
    ).strip() or project_id

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(files_dir.rglob("*")):
            if file_path.is_file():
                relative = file_path.relative_to(files_dir)
                arcname = f"{archive_name}/{str(relative).replace(chr(92), '/')}"
                zf.write(file_path, arcname)

    zip_buffer.seek(0)

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{archive_name}.zip"',
        },
    )


@router.get("/{project_id}/generated")
async def get_generated_files_summary(
    project_id: str,
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get a summary of generated files from the Engineer agent.
    """
    project, service = await _get_project_for_user(project_id, user)

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
