"""
Codebase Indexer - Indexes project files into the vector store.

Reads files from FileStore, splits them into chunks using
language-aware text splitters, and stores embeddings in ChromaDB.
"""

import logging
from datetime import datetime
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import (
    Language,
    RecursiveCharacterTextSplitter,
)

from app.config import get_settings
from app.rag.vector_store import get_vector_store
from app.storage import FileStore

logger = logging.getLogger(__name__)

# Map file extensions to LangChain Language enum for smart splitting
_LANGUAGE_MAP: dict[str, Language] = {
    ".py": Language.PYTHON,
    ".js": Language.JS,
    ".jsx": Language.JS,
    ".ts": Language.TS,
    ".tsx": Language.TS,
    ".html": Language.HTML,
    ".md": Language.MARKDOWN,
    ".go": Language.GO,
    ".rs": Language.RUST,
    ".java": Language.JAVA,
    ".rb": Language.RUBY,
    ".php": Language.PHP,
    ".swift": Language.SWIFT,
    ".kt": Language.KOTLIN,
    ".c": Language.C,
    ".cpp": Language.CPP,
    ".cs": Language.CSHARP,
    ".scala": Language.SCALA,
    ".lua": Language.LUA,
}

# File extensions/paths to skip during indexing
_SKIP_PATTERNS = {
    "node_modules",
    ".next",
    "__pycache__",
    ".git",
    "dist",
    "build",
    ".env",
    "package-lock.json",
    "yarn.lock",
    "uv.lock",
}

# Binary/non-text extensions to skip
_BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
    ".woff", ".woff2", ".ttf", ".eot",
    ".zip", ".tar", ".gz",
    ".pdf", ".doc", ".docx",
    ".mp3", ".mp4", ".wav",
}


class CodebaseIndexer:
    """
    Indexes project source code files into ChromaDB for retrieval.

    Handles:
    - Reading all project files from disk via FileStore
    - Language-aware chunking (splits at function/class boundaries)
    - Metadata attachment (file_path, language, chunk_index)
    - Incremental re-indexing of changed files
    """

    def __init__(self):
        self.file_store = FileStore()
        self.settings = get_settings()

    def _should_skip(self, file_path: str) -> bool:
        """Check if a file should be skipped during indexing."""
        # Skip binary files
        ext = Path(file_path).suffix.lower()
        if ext in _BINARY_EXTENSIONS:
            return True

        # Skip known non-useful paths
        parts = file_path.replace("\\", "/").split("/")
        for part in parts:
            if part in _SKIP_PATTERNS:
                return True

        return False

    def _get_splitter(self, file_path: str) -> RecursiveCharacterTextSplitter:
        """Get a language-aware text splitter for the file type."""
        ext = Path(file_path).suffix.lower()
        language = _LANGUAGE_MAP.get(ext)

        if language:
            return RecursiveCharacterTextSplitter.from_language(
                language=language,
                chunk_size=self.settings.rag_chunk_size,
                chunk_overlap=self.settings.rag_chunk_overlap,
            )

        # Fallback: generic splitter
        return RecursiveCharacterTextSplitter(
            chunk_size=self.settings.rag_chunk_size,
            chunk_overlap=self.settings.rag_chunk_overlap,
            separators=["\n\n", "\n", " ", ""],
        )

    async def index_project(self, project_id: str) -> dict:
        """
        Index all files in a project into the vector store.

        This performs a full re-index: clears existing data and re-embeds
        all project files.

        Args:
            project_id: Project identifier

        Returns:
            Dict with indexing stats (files_indexed, chunks_created, etc.)
        """
        logger.info(f"Starting full index for project {project_id}")

        # List all project files
        file_paths = await self.file_store.list_files(project_id)

        if not file_paths:
            logger.warning(f"No files found for project {project_id}")
            return {"files_indexed": 0, "chunks_created": 0, "skipped": 0}

        # Build documents from all files
        documents = []
        skipped = 0

        for file_path in file_paths:
            if self._should_skip(file_path):
                skipped += 1
                continue

            file_data = await self.file_store.read_file(project_id, file_path)
            if not file_data or not file_data.content.strip():
                skipped += 1
                continue

            # Get language-aware splitter
            splitter = self._get_splitter(file_path)

            # Split file content into chunks
            chunks = splitter.split_text(file_data.content)

            for i, chunk in enumerate(chunks):
                doc = Document(
                    page_content=chunk,
                    metadata={
                        "file_path": file_path,
                        "language": file_data.language,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "project_id": project_id,
                        "indexed_at": datetime.utcnow().isoformat(),
                    },
                )
                documents.append(doc)

        if not documents:
            logger.warning(f"No indexable content for project {project_id}")
            return {
                "files_indexed": 0,
                "chunks_created": 0,
                "skipped": skipped,
            }

        # Get vector store (creates if needed)
        vector_store = get_vector_store(project_id)

        # Clear existing collection data for a clean re-index
        try:
            existing = vector_store.get()
            if existing and existing.get("ids"):
                vector_store.delete(ids=existing["ids"])
        except Exception:
            pass  # Collection may be empty or not exist yet

        # Add documents to vector store
        vector_store.add_documents(documents)

        files_indexed = len(set(d.metadata["file_path"] for d in documents))

        logger.info(
            f"Indexed project {project_id}: "
            f"{files_indexed} files, {len(documents)} chunks, {skipped} skipped"
        )

        return {
            "files_indexed": files_indexed,
            "chunks_created": len(documents),
            "skipped": skipped,
        }

    async def reindex_files(
        self,
        project_id: str,
        file_paths: list[str],
    ) -> dict:
        """
        Re-index specific files that were changed.

        Only updates embeddings for the given files — much faster than
        a full re-index for chat-based incremental updates.

        Args:
            project_id: Project identifier
            file_paths: List of file paths that changed

        Returns:
            Dict with re-indexing stats
        """
        if not file_paths:
            return {"files_reindexed": 0, "chunks_created": 0}

        logger.info(
            f"Re-indexing {len(file_paths)} files for project {project_id}"
        )

        vector_store = get_vector_store(project_id)

        # Delete existing chunks for these files
        try:
            existing = vector_store.get(
                where={"file_path": {"$in": file_paths}}
            )
            if existing and existing.get("ids"):
                vector_store.delete(ids=existing["ids"])
        except Exception:
            pass  # May not exist yet

        # Re-index the changed files
        documents = []
        for file_path in file_paths:
            if self._should_skip(file_path):
                continue

            file_data = await self.file_store.read_file(project_id, file_path)
            if not file_data or not file_data.content.strip():
                continue

            splitter = self._get_splitter(file_path)
            chunks = splitter.split_text(file_data.content)

            for i, chunk in enumerate(chunks):
                doc = Document(
                    page_content=chunk,
                    metadata={
                        "file_path": file_path,
                        "language": file_data.language,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "project_id": project_id,
                        "indexed_at": datetime.utcnow().isoformat(),
                    },
                )
                documents.append(doc)

        if documents:
            vector_store.add_documents(documents)

        files_reindexed = len(set(d.metadata["file_path"] for d in documents))

        logger.info(
            f"Re-indexed {files_reindexed} files, "
            f"{len(documents)} chunks for project {project_id}"
        )

        return {
            "files_reindexed": files_reindexed,
            "chunks_created": len(documents),
        }

    async def get_index_status(self, project_id: str) -> dict:
        """
        Get indexing status for a project.

        Args:
            project_id: Project identifier

        Returns:
            Dict with status info (total_chunks, indexed_files, etc.)
        """
        try:
            vector_store = get_vector_store(project_id)
            collection_data = vector_store.get()

            if not collection_data or not collection_data.get("ids"):
                return {
                    "indexed": False,
                    "total_chunks": 0,
                    "indexed_files": [],
                    "last_indexed": None,
                }

            # Extract unique file paths and latest indexed timestamp
            metadatas = collection_data.get("metadatas", [])
            file_paths = set()
            latest_time = None

            for meta in metadatas:
                if meta:
                    file_paths.add(meta.get("file_path", "unknown"))
                    ts = meta.get("indexed_at")
                    if ts and (latest_time is None or ts > latest_time):
                        latest_time = ts

            return {
                "indexed": True,
                "total_chunks": len(collection_data["ids"]),
                "indexed_files": sorted(file_paths),
                "file_count": len(file_paths),
                "last_indexed": latest_time,
            }

        except Exception as e:
            logger.error(f"Error getting index status: {e}")
            return {
                "indexed": False,
                "total_chunks": 0,
                "indexed_files": [],
                "error": str(e),
            }
