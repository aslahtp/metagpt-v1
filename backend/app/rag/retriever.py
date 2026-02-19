"""
Codebase Retriever - Retrieves relevant code from the vector store.

Given a user query, finds the most relevant code chunks and can
return either chunks or full file contents for context injection
into the LLM prompt.
"""

import logging
from dataclasses import dataclass

from app.config import get_settings
from app.rag.vector_store import get_vector_store
from app.storage import FileStore

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    """A retrieved code chunk with its metadata."""

    content: str
    file_path: str
    language: str
    chunk_index: int
    total_chunks: int
    relevance_score: float


class CodebaseRetriever:
    """
    Retrieves relevant code context from the indexed codebase.

    Used by ChatService and agents to understand what code already
    exists before making changes.
    """

    def __init__(self):
        self.file_store = FileStore()
        self.settings = get_settings()

    async def retrieve(
        self,
        project_id: str,
        query: str,
        k: int | None = None,
    ) -> list[RetrievedChunk]:
        """
        Retrieve the most relevant code chunks for a query.

        Uses similarity search against the project's vector store.

        Args:
            project_id: Project identifier
            query: User's query or message
            k: Number of chunks to retrieve (defaults to config rag_top_k)

        Returns:
            List of RetrievedChunk sorted by relevance
        """
        if not self.settings.rag_enabled:
            return []

        k = k or self.settings.rag_top_k

        try:
            vector_store = get_vector_store(project_id)

            # Similarity search with scores
            results = vector_store.similarity_search_with_relevance_scores(
                query, k=k
            )

            chunks = []
            for doc, score in results:
                chunks.append(
                    RetrievedChunk(
                        content=doc.page_content,
                        file_path=doc.metadata.get("file_path", "unknown"),
                        language=doc.metadata.get("language", "text"),
                        chunk_index=doc.metadata.get("chunk_index", 0),
                        total_chunks=doc.metadata.get("total_chunks", 1),
                        relevance_score=score,
                    )
                )

            logger.info(
                f"Retrieved {len(chunks)} chunks for project {project_id} "
                f"(query: {query[:50]}...)"
            )

            return chunks

        except Exception as e:
            logger.error(f"Retrieval error for project {project_id}: {e}")
            return []

    async def retrieve_files(
        self,
        project_id: str,
        query: str,
        k: int = 5,
    ) -> list[dict]:
        """
        Retrieve full file contents for the most relevant files.

        First finds relevant chunks, then deduplicates by file path
        and returns full file contents. This is useful when the agent
        needs the complete file context (not just fragments).

        Args:
            project_id: Project identifier
            query: User's query or message
            k: Maximum number of files to return

        Returns:
            List of dicts with file_path, content, language, relevance_score
        """
        # Get more chunks than needed to find diverse files
        chunks = await self.retrieve(project_id, query, k=k * 3)

        if not chunks:
            return []

        # Deduplicate by file path, keeping highest relevance score
        seen_files: dict[str, float] = {}
        for chunk in chunks:
            if chunk.file_path not in seen_files:
                seen_files[chunk.file_path] = chunk.relevance_score
            else:
                seen_files[chunk.file_path] = max(
                    seen_files[chunk.file_path], chunk.relevance_score
                )

        # Sort by relevance and take top-k files
        sorted_files = sorted(
            seen_files.items(), key=lambda x: x[1], reverse=True
        )[:k]

        # Read full file contents
        results = []
        for file_path, score in sorted_files:
            file_data = await self.file_store.read_file(project_id, file_path)
            if file_data:
                results.append({
                    "file_path": file_path,
                    "content": file_data.content,
                    "language": file_data.language,
                    "relevance_score": score,
                })

        return results

    def format_context(
        self,
        chunks: list[RetrievedChunk],
        max_chars: int = 12000,
    ) -> str:
        """
        Format retrieved chunks into a context string for LLM injection.

        Groups chunks by file and formats them clearly so the LLM
        can understand the codebase structure.

        Args:
            chunks: Retrieved code chunks
            max_chars: Maximum character limit for the context

        Returns:
            Formatted context string
        """
        if not chunks:
            return "No relevant code found in the project."

        # Group chunks by file
        files: dict[str, list[RetrievedChunk]] = {}
        for chunk in chunks:
            if chunk.file_path not in files:
                files[chunk.file_path] = []
            files[chunk.file_path].append(chunk)

        # Sort chunks within each file by chunk_index
        for file_chunks in files.values():
            file_chunks.sort(key=lambda c: c.chunk_index)

        # Build context string
        lines = []
        total_chars = 0

        for file_path, file_chunks in files.items():
            header = f"\n### File: {file_path} ({file_chunks[0].language})\n"

            if total_chars + len(header) > max_chars:
                break

            lines.append(header)
            total_chars += len(header)

            for chunk in file_chunks:
                chunk_text = f"```{chunk.language}\n{chunk.content}\n```\n"

                if total_chars + len(chunk_text) > max_chars:
                    lines.append("... (truncated)\n")
                    break

                lines.append(chunk_text)
                total_chars += len(chunk_text)

        return "".join(lines)

    def format_file_context(
        self,
        files: list[dict],
        max_chars: int = 15000,
    ) -> str:
        """
        Format full file contents into a context string.

        Args:
            files: List of file dicts from retrieve_files()
            max_chars: Maximum character limit

        Returns:
            Formatted context string with full file contents
        """
        if not files:
            return "No relevant files found in the project."

        lines = []
        total_chars = 0

        for f in files:
            header = f"\n### File: {f['file_path']} ({f['language']})\n"
            content = f"```{f['language']}\n{f['content']}\n```\n"
            section = header + content

            if total_chars + len(section) > max_chars:
                # Try adding just a summary
                summary = (
                    f"\n### File: {f['file_path']} ({f['language']}) "
                    f"— [content truncated, {len(f['content'])} chars]\n"
                )
                if total_chars + len(summary) <= max_chars:
                    lines.append(summary)
                break

            lines.append(section)
            total_chars += len(section)

        return "".join(lines)
