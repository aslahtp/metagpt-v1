"""
Pipeline Service - Orchestrates the complete agent workflow.

This service coordinates:
- Pipeline execution
- File generation
- State persistence
- Streaming updates
- RAG indexing after generation
"""

import logging
import uuid
from datetime import datetime
from typing import Any, AsyncGenerator

from app.graph import AgentPipeline, PipelineState
from app.rag.indexer import CodebaseIndexer
from app.schemas.agents import GeneratedFileSpec
from app.schemas.projects import (
    PipelineStage,
    PipelineStatus,
    Project,
    ProjectState,
)
from app.storage import FileStore, ProjectStore

logger = logging.getLogger(__name__)


class PipelineService:
    """
    Service for managing the agent pipeline.

    Coordinates between the LangGraph pipeline, storage, and file generation.
    """

    def __init__(self):
        """Initialize the pipeline service."""
        self.project_store = ProjectStore()
        self.file_store = FileStore()
        self.pipeline = AgentPipeline()
        self.indexer = CodebaseIndexer()

    async def create_project(self, prompt: str, user_id: str = "") -> Project:
        """
        Create a new project from a user prompt.

        Args:
            prompt: User's natural language prompt
            user_id: Owner user ID

        Returns:
            Created Project
        """
        project_id = str(uuid.uuid4())[:8]
        return await self.project_store.create(project_id, prompt, user_id=user_id)

    async def run_pipeline(
        self,
        project_id: str,
        prompt: str,
        context: str = "",
    ) -> Project:
        """
        Run the complete agent pipeline for a project.

        Streams through agents internally and persists state after each one
        so that polling clients can see real-time progress.

        Args:
            project_id: Project identifier
            prompt: User prompt
            context: Additional context

        Returns:
            Project with all agent outputs
        """
        # Get or create project
        project = await self.project_store.get(project_id)
        if not project:
            project = await self.project_store.create(project_id, prompt)

        agent_order = ["manager", "architect", "engineer", "qa"]
        started_at = datetime.utcnow()

        # Update status to running — manager is about to start
        await self.project_store.update_state(
            project_id,
            pipeline_status=PipelineStatus(
                stage=PipelineStage.MANAGER,
                progress=0,
                current_agent="manager",
                message="Running Manager agent...",
                started_at=started_at,
            ),
        )

        try:
            # Stream through agents, persisting state after each one
            async for event in self.pipeline.stream(project_id, prompt, context):
                node_name = event.get("node", "")
                update = event.get("update") or {}
                if not update:
                    continue
                progress = update.get("progress", 0)

                idx = agent_order.index(node_name) if node_name in agent_order else -1
                is_last = idx == len(agent_order) - 1

                if is_last:
                    # Last agent (QA) — mark pipeline as completed
                    await self.project_store.update_state(
                        project_id,
                        manager_output=update.get("manager_output"),
                        architect_output=update.get("architect_output"),
                        engineer_output=update.get("engineer_output"),
                        qa_output=update.get("qa_output"),
                        pipeline_status=PipelineStatus(
                            stage=PipelineStage.COMPLETED,
                            progress=100,
                            current_agent=None,
                            message="Pipeline completed successfully",
                            started_at=started_at,
                            completed_at=datetime.utcnow(),
                        ),
                    )
                else:
                    # Intermediate agent — set current_agent to the NEXT agent
                    next_agent = agent_order[idx + 1]
                    await self.project_store.update_state(
                        project_id,
                        manager_output=update.get("manager_output"),
                        architect_output=update.get("architect_output"),
                        engineer_output=update.get("engineer_output"),
                        qa_output=update.get("qa_output"),
                        pipeline_status=PipelineStatus(
                            stage=PipelineStage(next_agent),
                            progress=progress,
                            current_agent=next_agent,
                            message=f"Running {next_agent.title()} agent...",
                            started_at=started_at,
                        ),
                    )

                # Write files if engineer completed
                if node_name == "engineer" and update.get("engineer_output"):
                    for file_spec in update["engineer_output"].files:
                        await self.file_store.write_file(project_id, file_spec)

                    # Index files for RAG after writing
                    try:
                        await self.indexer.index_project(project_id)
                        logger.info(f"Indexed project {project_id} for RAG")
                    except Exception as e:
                        logger.warning(f"RAG indexing failed: {e}")

            # Return final project
            project = await self.project_store.get(project_id)
            return project

        except Exception as e:
            # Update status to error
            await self.project_store.update_state(
                project_id,
                pipeline_status=PipelineStatus(
                    stage=PipelineStage.ERROR,
                    progress=0,
                    message=str(e),
                ),
            )
            raise

    async def stream_pipeline(
        self,
        project_id: str,
        prompt: str,
        context: str = "",
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Stream pipeline execution with real-time updates.

        Args:
            project_id: Project identifier
            prompt: User prompt
            context: Additional context

        Yields:
            Updates after each agent execution
        """
        # Get or create project
        project = await self.project_store.get(project_id)
        if not project:
            project = await self.project_store.create(project_id, prompt)

        yield {
            "type": "pipeline_start",
            "project_id": project_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            async for event in self.pipeline.stream(project_id, prompt, context):
                node_name = event.get("node", "")
                update = event.get("update") or {}
                if not update:
                    continue

                # Persist state before yielding so it's ready if frontend fetches
                await self._persist_agent_output(project_id, node_name, update)

                # Write files if engineer completed (before yielding events)
                file_events = []
                if node_name == "engineer" and update.get("engineer_output"):
                    files = update["engineer_output"].files
                    for file_spec in files:
                        await self.file_store.write_file(project_id, file_spec)
                        file_events.append({
                            "type": "file_generated",
                            "file_path": file_spec.file_path,
                            "language": file_spec.file_language,
                            "timestamp": datetime.utcnow().isoformat(),
                        })

                # Yield agent completion event
                yield {
                    "type": "agent_complete",
                    "agent": node_name,
                    "update": self._serialize_update(update),
                    "timestamp": event.get("timestamp"),
                }

                # Yield file generation events
                for fe in file_events:
                    yield fe

            # Persist final completed status
            await self.project_store.update_state(
                project_id,
                pipeline_status=PipelineStatus(
                    stage=PipelineStage.COMPLETED,
                    progress=100,
                    message="Pipeline completed successfully",
                    completed_at=datetime.utcnow(),
                ),
            )

            yield {
                "type": "pipeline_complete",
                "project_id": project_id,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            await self.project_store.update_state(
                project_id,
                pipeline_status=PipelineStatus(
                    stage=PipelineStage.ERROR,
                    progress=0,
                    message=str(e),
                ),
            )
            yield {
                "type": "pipeline_error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
            raise

    async def _persist_agent_output(
        self,
        project_id: str,
        agent: str,
        update: dict[str, Any],
    ) -> None:
        """Persist agent output to project state."""
        stage_map = {
            "manager": PipelineStage.MANAGER,
            "architect": PipelineStage.ARCHITECT,
            "engineer": PipelineStage.ENGINEER,
            "qa": PipelineStage.QA,
        }

        if not update:
            update = {}
        progress = update.get("progress", 0)
        stage = stage_map.get(agent, PipelineStage.PENDING)

        await self.project_store.update_state(
            project_id,
            manager_output=update.get("manager_output"),
            architect_output=update.get("architect_output"),
            engineer_output=update.get("engineer_output"),
            qa_output=update.get("qa_output"),
            pipeline_status=PipelineStatus(
                stage=stage,
                progress=progress,
                current_agent=agent,
            ),
        )

    async def _process_pipeline_results(
        self,
        project_id: str,
        state: PipelineState,
    ) -> Project:
        """Process pipeline results and update project."""
        # Write generated files
        if state.get("engineer_output"):
            for file_spec in state["engineer_output"].files:
                await self.file_store.write_file(project_id, file_spec)

        # Update project state
        project = await self.project_store.update_state(
            project_id,
            manager_output=state.get("manager_output"),
            architect_output=state.get("architect_output"),
            engineer_output=state.get("engineer_output"),
            qa_output=state.get("qa_output"),
            pipeline_status=PipelineStatus(
                stage=PipelineStage.COMPLETED if not state.get("error") else PipelineStage.ERROR,
                progress=100 if not state.get("error") else state.get("progress", 0),
                message=state.get("error") or "Pipeline completed successfully",
                completed_at=datetime.utcnow(),
            ),
        )

        return project

    def _serialize_update(self, update: dict[str, Any]) -> dict[str, Any]:
        """Serialize update for JSON streaming."""
        result = {}
        for key, value in update.items():
            if hasattr(value, "model_dump"):
                result[key] = value.model_dump()
            else:
                result[key] = value
        return result

    async def get_project(self, project_id: str) -> Project | None:
        """Get a project by ID."""
        return await self.project_store.get(project_id)

    async def _restore_files_from_db(self, project_id: str) -> bool:
        """
        Restore project files from MongoDB to disk.

        When Cloud Run containers restart, ephemeral disk storage is lost.
        This rebuilds the disk cache from the engineer_output stored in MongoDB.

        Returns:
            True if files were restored, False if no data in DB.
        """
        project = await self.project_store.get(project_id)
        if not project or not project.state.engineer_output:
            return False

        files = project.state.engineer_output.files
        if not files:
            return False

        for file_spec in files:
            await self.file_store.write_file(project_id, file_spec)

        return True

    async def get_file_tree(self, project_id: str):
        """Get the file tree for a project, restoring from DB if needed."""
        tree = await self.file_store.get_file_tree(project_id)
        if tree is not None:
            return tree

        # Disk cache miss — restore from MongoDB
        restored = await self._restore_files_from_db(project_id)
        if not restored:
            return None

        return await self.file_store.get_file_tree(project_id)

    async def get_file(self, project_id: str, file_path: str):
        """Get a specific file from a project, restoring from DB if needed."""
        result = await self.file_store.read_file(project_id, file_path)
        if result is not None:
            return result

        # Disk cache miss — restore all project files from MongoDB
        restored = await self._restore_files_from_db(project_id)
        if not restored:
            return None

        return await self.file_store.read_file(project_id, file_path)

    async def list_projects(self, limit: int = 50, offset: int = 0, user_id: str | None = None):
        """List projects, optionally filtered by user."""
        return await self.project_store.list_projects(limit, offset, user_id=user_id)
