"""
Pipeline State Definition for LangGraph.

This module defines the state that flows through the agent pipeline.
State is persisted after each node for resumability.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from app.schemas.agents import (
    ArchitectOutput,
    EngineerOutput,
    ManagerOutput,
    QAOutput,
)


class PipelineState(TypedDict, total=False):
    """
    State that flows through the LangGraph pipeline.

    This state is passed between nodes and persisted after each step.
    """

    # Input
    project_id: str
    user_prompt: str
    context: str

    # Agent outputs
    manager_output: ManagerOutput | None
    architect_output: ArchitectOutput | None
    engineer_output: EngineerOutput | None
    qa_output: QAOutput | None

    # Pipeline tracking
    current_stage: Literal[
        "pending", "manager", "architect", "engineer", "qa", "completed", "error"
    ]
    progress: float
    error: str | None
    error_stage: str | None

    # Timing
    started_at: str | None
    completed_at: str | None

    # Execution history
    execution_log: list[dict[str, Any]]


def create_initial_state(
    project_id: str,
    user_prompt: str,
    context: str = "",
) -> PipelineState:
    """
    Create initial pipeline state from user input.

    Args:
        project_id: Unique project identifier
        user_prompt: User's natural language prompt
        context: Optional additional context

    Returns:
        Initial PipelineState ready for execution
    """
    return PipelineState(
        project_id=project_id,
        user_prompt=user_prompt,
        context=context,
        manager_output=None,
        architect_output=None,
        engineer_output=None,
        qa_output=None,
        current_stage="pending",
        progress=0.0,
        error=None,
        error_stage=None,
        started_at=datetime.utcnow().isoformat(),
        completed_at=None,
        execution_log=[],
    )


def state_to_dict(state: PipelineState) -> dict[str, Any]:
    """Convert pipeline state to serializable dict."""
    result = dict(state)

    # Convert Pydantic models to dicts
    if result.get("manager_output"):
        result["manager_output"] = result["manager_output"].model_dump()
    if result.get("architect_output"):
        result["architect_output"] = result["architect_output"].model_dump()
    if result.get("engineer_output"):
        result["engineer_output"] = result["engineer_output"].model_dump()
    if result.get("qa_output"):
        result["qa_output"] = result["qa_output"].model_dump()

    return result
