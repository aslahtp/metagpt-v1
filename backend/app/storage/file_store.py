"""
File Store - Manages generated file storage.

Handles writing generated code files to disk and building file trees.
"""

import hashlib
import os
from datetime import datetime
from pathlib import Path

from app.config import get_settings
from app.schemas.agents import GeneratedFileSpec
from app.schemas.files import FileMetadata, FileTree, FileTreeNode, GeneratedFile


class FileStore:
    """
    Storage for generated project files.

    Writes files to disk and maintains metadata.
    """

    def __init__(self):
        """Initialize the file store."""
        settings = get_settings()
        self.projects_dir = Path(settings.projects_dir)
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    def _get_project_files_dir(self, project_id: str) -> Path:
        """Get the files directory for a project."""
        return self.projects_dir / project_id / "files"

    def _get_file_path(self, project_id: str, file_path: str) -> Path:
        """Get the full disk path for a project file."""
        files_dir = self._get_project_files_dir(project_id)
        # Normalize the path
        clean_path = file_path.lstrip("/\\")
        return files_dir / clean_path

    async def write_file(
        self,
        project_id: str,
        file_spec: GeneratedFileSpec,
    ) -> FileMetadata:
        """
        Write a generated file to disk.

        Args:
            project_id: Project identifier
            file_spec: Generated file specification

        Returns:
            FileMetadata for the written file
        """
        file_path = self._get_file_path(project_id, file_spec.file_path)

        # Create parent directories
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the file
        with open(file_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(file_spec.file_content)

        # Calculate checksum
        checksum = hashlib.sha256(file_spec.file_content.encode()).hexdigest()[:16]

        return FileMetadata(
            path=file_spec.file_path,
            language=file_spec.file_language,
            purpose=file_spec.file_purpose,
            size_bytes=len(file_spec.file_content.encode()),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            checksum=checksum,
        )

    async def write_files(
        self,
        project_id: str,
        files: list[GeneratedFileSpec],
    ) -> list[FileMetadata]:
        """
        Write multiple generated files to disk.

        Args:
            project_id: Project identifier
            files: List of generated file specifications

        Returns:
            List of FileMetadata for written files
        """
        metadata_list = []
        for file_spec in files:
            metadata = await self.write_file(project_id, file_spec)
            metadata_list.append(metadata)
        return metadata_list

    async def read_file(
        self,
        project_id: str,
        file_path: str,
    ) -> GeneratedFile | None:
        """
        Read a project file from disk.

        Args:
            project_id: Project identifier
            file_path: Path to the file within the project

        Returns:
            GeneratedFile or None if not found
        """
        full_path = self._get_file_path(project_id, file_path)

        if not full_path.exists():
            return None

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Detect language from extension
            language = self._detect_language(file_path)

            return GeneratedFile(
                path=file_path,
                content=content,
                language=language,
                purpose="",  # Would need metadata store for this
            )
        except Exception:
            return None

    async def update_file(
        self,
        project_id: str,
        file_path: str,
        content: str,
    ) -> FileMetadata | None:
        """
        Update an existing file.

        Args:
            project_id: Project identifier
            file_path: Path to the file
            content: New file content

        Returns:
            Updated FileMetadata or None if file doesn't exist
        """
        full_path = self._get_file_path(project_id, file_path)

        if not full_path.exists():
            return None

        with open(full_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)

        checksum = hashlib.sha256(content.encode()).hexdigest()[:16]

        return FileMetadata(
            path=file_path,
            language=self._detect_language(file_path),
            purpose="",
            size_bytes=len(content.encode()),
            updated_at=datetime.utcnow(),
            checksum=checksum,
        )

    async def get_file_tree(self, project_id: str) -> FileTree | None:
        """
        Build the file tree for a project.

        Args:
            project_id: Project identifier

        Returns:
            FileTree or None if project doesn't exist
        """
        files_dir = self._get_project_files_dir(project_id)

        if not files_dir.exists():
            return None

        root_node, total_files, total_dirs = self._build_tree_node(files_dir, "")

        return FileTree(
            project_id=project_id,
            root=root_node,
            total_files=total_files,
            total_directories=total_dirs,
        )

    def _build_tree_node(
        self,
        dir_path: Path,
        relative_path: str,
    ) -> tuple[FileTreeNode, int, int]:
        """Recursively build a file tree node."""
        name = dir_path.name or "root"
        children = []
        total_files = 0
        total_dirs = 0

        try:
            for item in sorted(dir_path.iterdir()):
                item_relative = (
                    f"{relative_path}/{item.name}" if relative_path else item.name
                )

                if item.is_dir():
                    total_dirs += 1
                    child_node, child_files, child_dirs = self._build_tree_node(
                        item, item_relative
                    )
                    children.append(child_node)
                    total_files += child_files
                    total_dirs += child_dirs
                else:
                    total_files += 1
                    children.append(
                        FileTreeNode(
                            name=item.name,
                            path=item_relative,
                            type="file",
                            language=self._detect_language(item.name),
                            children=[],
                        )
                    )
        except PermissionError:
            pass

        return (
            FileTreeNode(
                name=name,
                path=relative_path or "/",
                type="directory",
                children=children,
            ),
            total_files,
            total_dirs,
        )

    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".html": "html",
            ".css": "css",
            ".scss": "scss",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".md": "markdown",
            ".sql": "sql",
            ".sh": "bash",
            ".bash": "bash",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "c",
            ".hpp": "cpp",
            ".rb": "ruby",
            ".php": "php",
            ".swift": "swift",
            ".kt": "kotlin",
            ".toml": "toml",
            ".ini": "ini",
            ".xml": "xml",
            ".env": "env",
        }

        ext = Path(file_path).suffix.lower()
        return ext_map.get(ext, "text")

    async def delete_file(self, project_id: str, file_path: str) -> bool:
        """
        Delete a file from the project.

        Args:
            project_id: Project identifier
            file_path: Path to the file

        Returns:
            True if deleted, False if not found
        """
        full_path = self._get_file_path(project_id, file_path)

        if not full_path.exists():
            return False

        full_path.unlink()
        return True

    async def list_files(self, project_id: str) -> list[str]:
        """
        List all file paths in a project.

        Args:
            project_id: Project identifier

        Returns:
            List of file paths
        """
        files_dir = self._get_project_files_dir(project_id)

        if not files_dir.exists():
            return []

        paths = []
        for file_path in files_dir.rglob("*"):
            if file_path.is_file():
                relative = file_path.relative_to(files_dir)
                paths.append(str(relative).replace("\\", "/"))

        return sorted(paths)
