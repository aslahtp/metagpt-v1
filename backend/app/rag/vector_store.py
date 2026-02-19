"""
Vector Store management for RAG.

Each project gets its own isolated ChromaDB collection persisted to disk.
Collections are stored under {PROJECTS_DIR}/{project_id}/vectordb/.
"""

import shutil
from pathlib import Path

from langchain_chroma import Chroma

from app.config import get_settings
from app.rag.embeddings import get_embeddings


def _get_vectordb_path(project_id: str) -> Path:
    """Get the ChromaDB persistence directory for a project."""
    settings = get_settings()
    return Path(settings.projects_dir) / project_id / "vectordb"


def get_vector_store(project_id: str) -> Chroma:
    """
    Get or create a ChromaDB vector store for a project.

    Each project has its own isolated collection so that retrieval
    is scoped to the project's codebase only.

    Args:
        project_id: Project identifier

    Returns:
        Chroma vector store instance
    """
    persist_dir = _get_vectordb_path(project_id)
    persist_dir.mkdir(parents=True, exist_ok=True)

    return Chroma(
        collection_name=f"project_{project_id}",
        embedding_function=get_embeddings(),
        persist_directory=str(persist_dir),
    )


def delete_vector_store(project_id: str) -> bool:
    """
    Delete the vector store for a project.

    Called when a project is deleted to clean up disk space.

    Args:
        project_id: Project identifier

    Returns:
        True if deleted, False if not found
    """
    persist_dir = _get_vectordb_path(project_id)
    if persist_dir.exists():
        shutil.rmtree(persist_dir)
        return True
    return False
