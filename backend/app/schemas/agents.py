"""Schemas for agent inputs and outputs."""

from typing import Any

from pydantic import BaseModel, Field


class Requirement(BaseModel):
    """A single requirement extracted by the Manager Agent."""

    id: str = Field(..., description="Unique requirement identifier")
    category: str = Field(..., description="Category: functional, non-functional, technical")
    description: str = Field(..., description="Detailed requirement description")
    priority: str = Field(..., description="Priority: high, medium, low")
    acceptance_criteria: list[str] = Field(
        default_factory=list, description="Criteria for requirement completion"
    )


class ManagerOutput(BaseModel):
    """Structured output from Manager Agent."""

    project_name: str = Field(..., description="Inferred project name")
    project_description: str = Field(..., description="High-level project description")
    project_type: str = Field(
        ..., description="Type: web-app, api, cli, library, mobile-app, other"
    )
    tech_stack: list[str] = Field(default_factory=list, description="Recommended technologies")
    requirements: list[Requirement] = Field(
        default_factory=list, description="Extracted requirements"
    )
    constraints: list[str] = Field(default_factory=list, description="Project constraints")
    assumptions: list[str] = Field(default_factory=list, description="Assumptions made")
    reasoning: str = Field(..., description="Agent's reasoning process")


class FileStructure(BaseModel):
    """A file in the planned architecture."""

    path: str = Field(..., description="File path relative to project root")
    purpose: str = Field(..., description="Purpose of this file")
    dependencies: list[str] = Field(default_factory=list, description="Files this depends on")


class Component(BaseModel):
    """A component in the system architecture."""

    name: str = Field(..., description="Component name")
    type: str = Field(..., description="Type: frontend, backend, database, service, utility")
    description: str = Field(..., description="Component description")
    technologies: list[str] = Field(default_factory=list, description="Technologies used")
    files: list[FileStructure] = Field(default_factory=list, description="Files in this component")


class ArchitectOutput(BaseModel):
    """Structured output from Architect Agent."""

    architecture_type: str = Field(..., description="Architecture pattern used")
    components: list[Component] = Field(default_factory=list, description="System components")
    file_structure: list[FileStructure] = Field(
        default_factory=list, description="Complete file structure"
    )
    data_flow: str = Field(..., description="Description of data flow")
    api_design: dict[str, Any] = Field(default_factory=dict, description="API endpoints design")
    database_schema: dict[str, Any] = Field(
        default_factory=dict, description="Database schema if applicable"
    )
    deployment_notes: str = Field(default="", description="Deployment considerations")
    reasoning: str = Field(..., description="Agent's reasoning process")


class GeneratedFileSpec(BaseModel):
    """Specification for a generated file."""

    file_path: str = Field(..., description="Full file path")
    file_content: str = Field(..., description="Complete file content")
    file_language: str = Field(..., description="Programming language or file type")
    file_purpose: str = Field(..., description="Purpose of this file")


class EngineerOutput(BaseModel):
    """Structured output from Engineer Agent."""

    files: list[GeneratedFileSpec] = Field(default_factory=list, description="Generated files")
    implementation_notes: str = Field(..., description="Implementation details and decisions")
    dependencies_added: list[str] = Field(
        default_factory=list, description="External dependencies required"
    )
    setup_instructions: list[str] = Field(
        default_factory=list, description="Setup and run instructions"
    )
    reasoning: str = Field(..., description="Agent's reasoning process")


class TestCase(BaseModel):
    """A test case specification."""

    id: str = Field(..., description="Test case identifier")
    name: str = Field(..., description="Test case name")
    description: str = Field(..., description="What is being tested")
    test_type: str = Field(..., description="Type: unit, integration, e2e, manual")
    target_file: str = Field(..., description="File being tested")
    test_code: str = Field(default="", description="Test code if applicable")
    steps: list[str] = Field(default_factory=list, description="Manual test steps if applicable")
    expected_result: str = Field(..., description="Expected outcome")


class ValidationNote(BaseModel):
    """A validation note or issue found."""

    severity: str = Field(..., description="Severity: error, warning, info")
    category: str = Field(
        ..., description="Category: security, performance, maintainability, functionality"
    )
    file_path: str = Field(default="", description="Related file if applicable")
    description: str = Field(..., description="Issue description")
    recommendation: str = Field(..., description="Recommended fix or action")


class QAOutput(BaseModel):
    """Structured output from QA Agent."""

    test_cases: list[TestCase] = Field(default_factory=list, description="Test cases")
    validation_notes: list[ValidationNote] = Field(
        default_factory=list, description="Validation findings"
    )
    code_review_summary: str = Field(..., description="Overall code review summary")
    test_coverage_estimate: str = Field(..., description="Estimated test coverage")
    quality_score: int = Field(..., ge=0, le=100, description="Quality score 0-100")
    approval_status: str = Field(
        ..., description="Status: approved, needs-revision, rejected"
    )
    reasoning: str = Field(..., description="Agent's reasoning process")


class AgentOutput(BaseModel):
    """Generic wrapper for any agent output with metadata."""

    agent_name: str = Field(..., description="Name of the agent")
    status: str = Field(..., description="Status: success, error, partial")
    output: ManagerOutput | ArchitectOutput | EngineerOutput | QAOutput = Field(
        ..., description="Agent-specific output"
    )
    execution_time_ms: int = Field(..., description="Execution time in milliseconds")
    token_usage: dict[str, int] = Field(
        default_factory=dict, description="Token usage statistics"
    )
