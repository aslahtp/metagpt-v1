"""
Project Store - Manages project state persistence.

Supports both file-based and in-memory storage.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.schemas.projects import (
    PipelineStage,
    PipelineStatus,
    PreviewMetadata,
    Project,
    ProjectState,
)
from app.schemas.agents import (
    ArchitectOutput,
    EngineerOutput,
    ManagerOutput,
    QAOutput,
)


class ProjectStore:
    """
    Persistent storage for project state and metadata.

    Stores projects as JSON files in the projects directory.
    """

    def __init__(self):
        """Initialize the project store."""
        settings = get_settings()
        self.projects_dir = Path(settings.projects_dir)
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, Project] = {}

    def _get_project_dir(self, project_id: str) -> Path:
        """Get the directory for a specific project."""
        return self.projects_dir / project_id

    def _get_state_file(self, project_id: str) -> Path:
        """Get the state file path for a project."""
        return self._get_project_dir(project_id) / "project.json"

    async def create(self, project_id: str, prompt: str) -> Project:
        """
        Create a new project.

        Args:
            project_id: Unique project identifier
            prompt: User's original prompt

        Returns:
            Created Project instance
        """
        project_dir = self._get_project_dir(project_id)
        project_dir.mkdir(parents=True, exist_ok=True)

        project = Project(
            id=project_id,
            prompt=prompt,
            state=ProjectState(
                pipeline_status=PipelineStatus(
                    stage=PipelineStage.PENDING,
                    progress=0,
                )
            ),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        await self.save(project)
        return project

    async def get(self, project_id: str) -> Project | None:
        """
        Get a project by ID.

        Args:
            project_id: Project identifier

        Returns:
            Project if found, None otherwise
        """
        # Check cache first
        if project_id in self._cache:
            return self._cache[project_id]

        state_file = self._get_state_file(project_id)
        if not state_file.exists():
            return None

        try:
            with open(state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            project = self._deserialize_project(data)
            self._cache[project_id] = project
            return project
        except Exception:
            return None

    async def save(self, project: Project) -> None:
        """
        Save a project to disk.

        Args:
            project: Project to save
        """
        project.updated_at = datetime.utcnow()

        state_file = self._get_state_file(project.id)
        state_file.parent.mkdir(parents=True, exist_ok=True)

        data = self._serialize_project(project)
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

        self._cache[project.id] = project

    async def update_state(
        self,
        project_id: str,
        manager_output: ManagerOutput | None = None,
        architect_output: ArchitectOutput | None = None,
        engineer_output: EngineerOutput | None = None,
        qa_output: QAOutput | None = None,
        pipeline_status: PipelineStatus | None = None,
    ) -> Project | None:
        """
        Update project state with agent outputs.

        Args:
            project_id: Project identifier
            manager_output: Manager agent output
            architect_output: Architect agent output
            engineer_output: Engineer agent output
            qa_output: QA agent output
            pipeline_status: Pipeline execution status

        Returns:
            Updated project or None if not found
        """
        project = await self.get(project_id)
        if not project:
            return None

        if manager_output:
            project.state.manager_output = manager_output
            project.name = manager_output.project_name
            project.description = manager_output.project_description

        if architect_output:
            project.state.architect_output = architect_output

        if engineer_output:
            project.state.engineer_output = engineer_output
            # Detect if this is a React/Next.js project
            project.preview = self._detect_preview_support(engineer_output)

        if qa_output:
            project.state.qa_output = qa_output

        if pipeline_status:
            project.state.pipeline_status = pipeline_status

        await self.save(project)
        return project

    def _detect_preview_support(self, engineer_output: EngineerOutput) -> PreviewMetadata:
        """Detect if the project supports preview (React/Next.js)."""
        is_react = False
        is_nextjs = False
        entry_file = None
        framework = None

        for file in engineer_output.files:
            path_lower = file.file_path.lower()
            content_lower = file.file_content.lower()

            # Check for React
            if "react" in content_lower or "jsx" in file.file_language.lower():
                is_react = True
                framework = "React"

            # Check for Next.js
            if "next" in path_lower or "next/app" in content_lower:
                is_nextjs = True
                is_react = True
                framework = "Next.js"

            # Find entry file
            if any(name in path_lower for name in ["app.tsx", "app.jsx", "index.tsx", "page.tsx"]):
                entry_file = file.file_path

        return PreviewMetadata(
            is_react_project=is_react,
            is_nextjs_project=is_nextjs,
            entry_file=entry_file,
            preview_supported=is_react,
            framework=framework,
        )

    async def list_projects(self, limit: int = 50, offset: int = 0) -> list[Project]:
        """
        List all projects.

        Args:
            limit: Maximum number of projects to return
            offset: Number of projects to skip

        Returns:
            List of projects
        """
        projects = []
        if not self.projects_dir.exists():
            return projects

        project_dirs = sorted(
            [d for d in self.projects_dir.iterdir() if d.is_dir()],
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )

        for project_dir in project_dirs[offset : offset + limit]:
            project = await self.get(project_dir.name)
            if project:
                projects.append(project)

        return projects

    async def delete(self, project_id: str) -> bool:
        """
        Delete a project.

        Args:
            project_id: Project identifier

        Returns:
            True if deleted, False if not found
        """
        import shutil

        project_dir = self._get_project_dir(project_id)
        if not project_dir.exists():
            return False

        shutil.rmtree(project_dir)
        self._cache.pop(project_id, None)
        return True

    def _serialize_project(self, project: Project) -> dict[str, Any]:
        """Serialize project to JSON-compatible dict."""
        return project.model_dump(mode="json")

    def _deserialize_project(self, data: dict[str, Any]) -> Project:
        """Deserialize project from dict."""
        # Handle nested state objects
        if "state" in data:
            state_data = data["state"]

            if state_data.get("manager_output"):
                state_data["manager_output"] = ManagerOutput(**state_data["manager_output"])

            if state_data.get("architect_output"):
                state_data["architect_output"] = ArchitectOutput(**state_data["architect_output"])

            if state_data.get("engineer_output"):
                state_data["engineer_output"] = EngineerOutput(**state_data["engineer_output"])

            if state_data.get("qa_output"):
                state_data["qa_output"] = QAOutput(**state_data["qa_output"])

            if state_data.get("pipeline_status"):
                state_data["pipeline_status"] = PipelineStatus(**state_data["pipeline_status"])

            data["state"] = ProjectState(**state_data)

        if "preview" in data:
            data["preview"] = PreviewMetadata(**data["preview"])

        return Project(**data)
