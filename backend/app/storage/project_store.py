"""
Project Store - Manages project state persistence via MongoDB.

Uses Beanie ODM for async MongoDB operations.
"""

from datetime import datetime

from app.models.project import ProjectDocument
from app.schemas.agents import (
    ArchitectOutput,
    EngineerOutput,
    ManagerOutput,
    QAOutput,
)
from app.schemas.projects import (
    PipelineStage,
    PipelineStatus,
    PreviewMetadata,
    Project,
    ProjectState,
)


class ProjectStore:
    """
    Persistent storage for project state and metadata using MongoDB.
    """

    async def create(self, project_id: str, prompt: str, user_id: str = "") -> Project:
        """
        Create a new project.

        Args:
            project_id: Unique project identifier
            prompt: User's original prompt
            user_id: Owner user ID

        Returns:
            Created Project instance (API schema)
        """
        doc = ProjectDocument(
            project_id=project_id,
            user_id=user_id,
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
        await doc.insert()
        return self._to_project(doc)

    async def get(self, project_id: str) -> Project | None:
        """
        Get a project by its short ID.

        Args:
            project_id: Project identifier

        Returns:
            Project if found, None otherwise
        """
        doc = await ProjectDocument.find_one(ProjectDocument.project_id == project_id)
        if not doc:
            return None
        return self._to_project(doc)

    async def save(self, project: Project) -> None:
        """
        Save/update a project in MongoDB.

        Args:
            project: Project to save (API schema)
        """
        doc = await ProjectDocument.find_one(ProjectDocument.project_id == project.id)
        if not doc:
            doc = ProjectDocument(
                project_id=project.id,
                user_id=project.user_id,
                prompt=project.prompt,
                name=project.name,
                description=project.description,
                state=project.state,
                preview=project.preview,
                created_at=project.created_at,
                updated_at=datetime.utcnow(),
                version=project.version,
            )
            await doc.insert()
        else:
            doc.name = project.name
            doc.description = project.description
            doc.state = project.state
            doc.preview = project.preview
            doc.updated_at = datetime.utcnow()
            doc.version = project.version
            await doc.save()

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
        doc = await ProjectDocument.find_one(ProjectDocument.project_id == project_id)
        if not doc:
            return None

        if manager_output:
            doc.state.manager_output = manager_output
            doc.name = manager_output.project_name
            doc.description = manager_output.project_description

        if architect_output:
            doc.state.architect_output = architect_output

        if engineer_output:
            doc.state.engineer_output = engineer_output
            doc.preview = self._detect_preview_support(engineer_output)

        if qa_output:
            doc.state.qa_output = qa_output

        if pipeline_status:
            doc.state.pipeline_status = pipeline_status

        doc.updated_at = datetime.utcnow()
        await doc.save()

        return self._to_project(doc)

    def _detect_preview_support(self, engineer_output: EngineerOutput) -> PreviewMetadata:
        """Detect if the project supports preview (React/Next.js)."""
        is_react = False
        is_nextjs = False
        entry_file = None
        framework = None

        for file in engineer_output.files:
            path_lower = file.file_path.lower()
            content_lower = file.file_content.lower()

            if "react" in content_lower or "jsx" in file.file_language.lower():
                is_react = True
                framework = "React"

            if "next" in path_lower or "next/app" in content_lower:
                is_nextjs = True
                is_react = True
                framework = "Next.js"

            if any(
                name in path_lower
                for name in ["app.tsx", "app.jsx", "index.tsx", "page.tsx"]
            ):
                entry_file = file.file_path

        return PreviewMetadata(
            is_react_project=is_react,
            is_nextjs_project=is_nextjs,
            entry_file=entry_file,
            preview_supported=is_react,
            framework=framework,
        )

    async def list_projects(
        self, limit: int = 50, offset: int = 0, user_id: str | None = None
    ) -> list[Project]:
        """
        List projects, optionally filtered by user.

        Args:
            limit: Maximum number of projects to return
            offset: Number of projects to skip
            user_id: If provided, only return projects for this user

        Returns:
            List of projects
        """
        query = ProjectDocument.find()
        if user_id:
            query = ProjectDocument.find(ProjectDocument.user_id == user_id)

        docs = (
            await query.sort(-ProjectDocument.updated_at).skip(offset).limit(limit).to_list()
        )

        return [self._to_project(doc) for doc in docs]

    async def delete(self, project_id: str) -> bool:
        """
        Delete a project.

        Args:
            project_id: Project identifier

        Returns:
            True if deleted, False if not found
        """
        doc = await ProjectDocument.find_one(ProjectDocument.project_id == project_id)
        if not doc:
            return False
        await doc.delete()
        return True

    def _to_project(self, doc: ProjectDocument) -> Project:
        """Convert a ProjectDocument to the API Project schema."""
        return Project(
            id=doc.project_id,
            user_id=doc.user_id,
            prompt=doc.prompt,
            name=doc.name,
            description=doc.description,
            state=doc.state,
            preview=doc.preview,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
            version=doc.version,
        )
