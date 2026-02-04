"""Schemas for file operations and storage."""

from datetime import datetime

from pydantic import BaseModel, Field


class FileMetadata(BaseModel):
    """Metadata for a generated file."""

    path: str = Field(..., description="File path relative to project root")
    language: str = Field(..., description="Programming language or file type")
    purpose: str = Field(..., description="Purpose of this file")
    size_bytes: int = Field(..., description="File size in bytes")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    checksum: str = Field(default="", description="File content hash")


class GeneratedFile(BaseModel):
    """A generated file with content."""

    path: str = Field(..., description="File path relative to project root")
    content: str = Field(..., description="File content")
    language: str = Field(..., description="Programming language or file type")
    purpose: str = Field(..., description="Purpose of this file")


class FileTreeNode(BaseModel):
    """A node in the file tree."""

    name: str = Field(..., description="File or directory name")
    path: str = Field(..., description="Full path")
    type: str = Field(..., description="Type: file or directory")
    language: str | None = Field(None, description="Language for files")
    children: list["FileTreeNode"] = Field(default_factory=list, description="Child nodes")


class FileTree(BaseModel):
    """Complete file tree for a project."""

    project_id: str = Field(..., description="Project identifier")
    root: FileTreeNode = Field(..., description="Root node of file tree")
    total_files: int = Field(..., description="Total number of files")
    total_directories: int = Field(..., description="Total number of directories")
