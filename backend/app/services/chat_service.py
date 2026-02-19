"""
Chat Service - Handles iterative chat-based updates.

Uses RAG to retrieve relevant code context, then makes a single
direct LLM call to produce targeted file edits. Does NOT re-run
the full agent pipeline.
"""

import json
import logging
import re
import uuid
from datetime import datetime
from typing import Any

from langchain_core.messages import HumanMessage

from app.config import get_settings
from app.rag.retriever import CodebaseRetriever
from app.schemas.agents import EngineerOutput, GeneratedFileSpec
from app.schemas.projects import ChatMessage, ChatRequest, ChatResponse
from app.storage import FileStore, ProjectStore

logger = logging.getLogger(__name__)


CHAT_EDIT_PROMPT = """You are a code-editing assistant. The user wants to make a change to their existing project.

## User Request
{message}

## Existing Project Files
Below are the current contents of the project files most relevant to the request.
{file_context}

## All Project Files
These are ALL file paths in the project (for awareness):
{all_file_paths}

## Instructions
1. Analyze the user's request and determine which files need to change.
2. Return ONLY the files that need modification, with their COMPLETE updated contents.
3. Do NOT return files that don't need changes.
4. Make targeted, minimal edits — preserve existing code structure and style.
5. If the request involves styling/colors, focus on CSS/style files.
6. Ensure the modified code is complete and functional — no placeholders.

## Response Format
Respond with ONLY a JSON object in this exact format:
{{
    "summary": "Brief description of what was changed",
    "files": [
        {{
            "file_path": "path/to/file.ext",
            "file_content": "complete updated file content here",
            "file_language": "language",
            "file_purpose": "brief purpose"
        }}
    ]
}}

CRITICAL: Return the COMPLETE file content for each modified file, not just the changed parts.
Return ONLY valid JSON, no markdown fences, no extra text."""


class ChatService:
    """
    Service for handling chat-based project iterations.

    Uses RAG to identify relevant files, reads their full contents,
    then makes a single LLM call to get targeted edits.
    """

    def __init__(self, model: str | None = None):
        """Initialize the chat service."""
        self.file_store = FileStore()
        self.retriever = CodebaseRetriever()
        self.settings = get_settings()
        self._model = model
        self.llm = self._create_llm(model)

    def _create_llm(self, model: str | None = None):
        """Create an LLM instance with a generous timeout for chat."""
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=model or self.settings.llm_model,
            google_api_key=self.settings.google_api_key,
            timeout=300,  # 5 min — chat prompts are large
            temperature=0.3,
            convert_system_message_to_human=True,
        )

    async def process_message(
        self,
        project_id: str,
        request: ChatRequest,
    ) -> ChatResponse:
        """
        Process a chat message and update the project.

        Flow: RAG retrieval -> Read files -> Single LLM call -> Write changes
        """
        if request.model:
            self.llm = self._create_llm(request.model)

        logger.info(f"Processing chat for project {project_id}: {request.message[:80]}")

        # Step 1: Get all file paths in the project
        all_file_paths = await self.file_store.list_files(project_id)
        if not all_file_paths:
            raise ValueError(f"Project {project_id} has no files")

        # Step 2: Use RAG to find relevant files, then read full contents
        file_context = await self._get_file_context(
            project_id, request.message, all_file_paths
        )

        # Step 3: Single LLM call for targeted edits
        llm_result = await self._call_llm(
            request.message, file_context, all_file_paths
        )

        # Step 4: Write modified files to disk and collect specs
        files_modified = []
        modified_specs = []
        for file_data in llm_result.get("files", []):
            try:
                file_spec = GeneratedFileSpec(
                    file_path=file_data["file_path"],
                    file_content=file_data["file_content"],
                    file_language=file_data.get("file_language", "text"),
                    file_purpose=file_data.get("file_purpose", ""),
                )
                await self.file_store.write_file(project_id, file_spec)
                files_modified.append(file_spec.file_path)
                modified_specs.append(file_spec)
                logger.info(f"  Updated: {file_spec.file_path}")
            except Exception as e:
                logger.error(f"  Failed to write {file_data.get('file_path')}: {e}")

        # Step 5: Update MongoDB with the modified engineer output
        if files_modified:
            await self._update_project_state(project_id, modified_specs)

        # Step 6: Build response
        summary = llm_result.get("summary", "Changes applied.")
        if files_modified:
            files_list = "\n".join(f"- {f}" for f in files_modified)
            response_content = f"{summary}\n\nUpdated files:\n{files_list}"
        else:
            response_content = summary

        logger.info(f"Chat complete: {len(files_modified)} files modified")

        response_message = ChatMessage(
            id=str(uuid.uuid4())[:8],
            role="assistant",
            content=response_content,
            timestamp=datetime.utcnow(),
            agent_triggered="engineer",
            files_modified=files_modified,
        )

        return ChatResponse(
            message=response_message,
            agents_executed=["engineer"] if files_modified else [],
            files_modified=files_modified,
            files_referenced=[],
            project_updated=len(files_modified) > 0,
        )

    async def _get_file_context(
        self,
        project_id: str,
        message: str,
        all_file_paths: list[str],
    ) -> str:
        """Build file context for the LLM prompt.

        For small projects (<=30 files): include ALL files — gives LLM full picture.
        For large projects: use RAG to select the most relevant files.
        """

        # Small projects: just include everything
        if len(all_file_paths) <= 30:
            logger.info(
                f"Small project ({len(all_file_paths)} files), including all"
            )
            return await self._read_all_files(project_id, all_file_paths)

        # Large projects: use RAG for smart file selection
        if self.settings.rag_enabled:
            try:
                relevant_files = await self.retriever.retrieve_files(
                    project_id, message, k=15
                )
                if relevant_files:
                    rag_paths = {f["file_path"] for f in relevant_files}
                    logger.info(
                        f"RAG identified {len(rag_paths)} relevant files: {rag_paths}"
                    )

                    context_parts = []
                    for f in relevant_files:
                        context_parts.append(
                            f"### {f['file_path']} ({f['language']})\n"
                            f"```{f['language']}\n{f['content']}\n```"
                        )
                    return "\n\n".join(context_parts)
            except Exception as e:
                logger.warning(f"RAG retrieval failed, falling back: {e}")

        # Fallback: read all files with a size cap
        return await self._read_all_files(project_id, all_file_paths)

    async def _read_all_files(
        self,
        project_id: str,
        file_paths: list[str],
        max_chars: int = 120000,
    ) -> str:
        """Read all project files into a context string."""
        context_parts = []
        total_chars = 0

        for file_path in file_paths:
            file_data = await self.file_store.read_file(project_id, file_path)
            if file_data and file_data.content:
                section = (
                    f"### {file_path} ({file_data.language})\n"
                    f"```{file_data.language}\n{file_data.content}\n```"
                )
                if total_chars + len(section) > max_chars:
                    context_parts.append(f"### {file_path} — [truncated]")
                    break
                context_parts.append(section)
                total_chars += len(section)

        return "\n\n".join(context_parts)

    async def _call_llm(
        self,
        message: str,
        file_context: str,
        all_file_paths: list[str],
    ) -> dict[str, Any]:
        """Make a single LLM call to get targeted file edits."""

        prompt = CHAT_EDIT_PROMPT.format(
            message=message,
            file_context=file_context,
            all_file_paths="\n".join(f"- {p}" for p in all_file_paths),
        )

        logger.info("Calling LLM for targeted edits...")

        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            raw = response.content
            # Gemini may return content as a list of parts
            if isinstance(raw, list):
                content = "".join(
                    part if isinstance(part, str) else part.get("text", "")
                    for part in raw
                ).strip()
            else:
                content = raw.strip()

            # Strip markdown fences if present
            if content.startswith("```"):
                content = re.sub(r"^```(?:json)?\s*\n?", "", content)
                content = re.sub(r"\n?```\s*$", "", content)

            result = json.loads(content)
            files_count = len(result.get("files", []))
            logger.info(f"LLM returned {files_count} files to update")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            logger.error(f"Raw response: {content[:500]}")
            return {
                "summary": "Failed to parse the response. Please try again.",
                "files": [],
            }
        except Exception as e:
            logger.error(f"LLM call failed: {e}", exc_info=True)
            return {"summary": f"Error: {str(e)}", "files": []}

    async def _update_project_state(
        self,
        project_id: str,
        modified_specs: list[GeneratedFileSpec],
    ) -> None:
        """Update the engineer output in MongoDB with modified files."""
        try:
            project_store = ProjectStore()
            project = await project_store.get(project_id)
            if not project:
                logger.warning(f"Project {project_id} not found in MongoDB")
                return

            # Get existing engineer output files
            existing_output = project.state.engineer_output
            if existing_output:
                # Build a map of existing files
                files_map = {f.file_path: f for f in existing_output.files}
                # Update/add modified files
                for spec in modified_specs:
                    files_map[spec.file_path] = spec
                # Create updated engineer output
                updated_output = EngineerOutput(
                    files=list(files_map.values()),
                    implementation_notes=existing_output.implementation_notes,
                    dependencies_added=existing_output.dependencies_added,
                    setup_instructions=existing_output.setup_instructions,
                    reasoning=existing_output.reasoning,
                )
            else:
                # No existing output — create fresh
                updated_output = EngineerOutput(
                    files=modified_specs,
                    implementation_notes="Updated via chat",
                    dependencies_added=[],
                    setup_instructions=[],
                    reasoning="Chat-based file update",
                )

            await project_store.update_state(
                project_id, engineer_output=updated_output
            )
            logger.info(f"Updated MongoDB for project {project_id}")

        except Exception as e:
            logger.error(f"Failed to update MongoDB: {e}", exc_info=True)

    async def get_chat_history(
        self,
        project_id: str,
        limit: int = 50,
    ) -> list[ChatMessage]:
        """Get chat history for a project."""
        return []
