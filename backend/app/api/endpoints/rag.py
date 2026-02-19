"""RAG endpoints for codebase indexing and retrieval."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.auth import get_current_user
from app.models.user import User
from app.rag.indexer import CodebaseIndexer
from app.rag.retriever import CodebaseRetriever
from app.services import PipelineService

router = APIRouter()


class RAGQueryRequest(BaseModel):
    """Request to query the RAG index."""

    query: str = Field(..., min_length=1, description="Search query")
    k: int = Field(default=8, ge=1, le=20, description="Number of results")


async def _verify_project_owner(project_id: str, user: User):
    """Verify the project exists and belongs to the user."""
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


@router.post("/{project_id}/index")
async def index_project(
    project_id: str,
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Trigger (re-)indexing of a project's codebase for RAG.
    """
    await _verify_project_owner(project_id, user)

    indexer = CodebaseIndexer()

    try:
        stats = await indexer.index_project(project_id)
        return {
            "project_id": project_id,
            "status": "indexed",
            **stats,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Indexing failed: {str(e)}",
        )


@router.get("/{project_id}/status")
async def get_index_status(
    project_id: str,
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get RAG indexing status for a project.
    """
    await _verify_project_owner(project_id, user)

    indexer = CodebaseIndexer()

    try:
        status_info = await indexer.get_index_status(project_id)
        return {
            "project_id": project_id,
            **status_info,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/{project_id}/query")
async def query_codebase(
    project_id: str,
    request: RAGQueryRequest,
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Query the RAG index for relevant code chunks.

    Useful for debugging and testing RAG retrieval quality.
    """
    await _verify_project_owner(project_id, user)

    retriever = CodebaseRetriever()

    try:
        chunks = await retriever.retrieve(project_id, request.query, k=request.k)

        return {
            "project_id": project_id,
            "query": request.query,
            "results": [
                {
                    "file_path": chunk.file_path,
                    "language": chunk.language,
                    "content": chunk.content,
                    "chunk_index": chunk.chunk_index,
                    "relevance_score": chunk.relevance_score,
                }
                for chunk in chunks
            ],
            "total": len(chunks),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}",
        )
