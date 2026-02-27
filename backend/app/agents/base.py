"""
Base Agent Class - Foundation for all SOP-driven agents.

All agents inherit from this base class which provides:
- Centralized LLM access (Gemini Model)
- SOP loading and formatting
- Structured output parsing
- Execution tracking and logging
"""

import json
import time
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from app.llm import get_llm, get_llm_with_structured_output
from app.sop import AgentSOP

T = TypeVar("T", bound=BaseModel)


class BaseAgent(ABC, Generic[T]):
    """
    Base class for all SOP-driven agents.

    All agents use Gemini Model via LangChain as configured in the llm module.
    Each agent operates according to its SOP (Standard Operating Procedure).
    """

    def __init__(self, sop: AgentSOP, output_schema: type[T]):
        """
        Initialize the agent with its SOP and output schema.

        Args:
            sop: The Standard Operating Procedure for this agent
            output_schema: Pydantic model for structured output
        """
        self.sop = sop
        self.output_schema = output_schema
        self._execution_stats: dict[str, Any] = {}

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent name for logging and tracking."""
        pass

    @abstractmethod
    def _build_prompt(self, **inputs: Any) -> str:
        """
        Build the prompt from SOP template and inputs.

        Args:
            **inputs: Agent-specific inputs

        Returns:
            Formatted prompt string
        """
        pass

    def _format_sop_section(self, items: list[str]) -> str:
        """Format a list of SOP items as a numbered list."""
        return "\n".join(f"{i+1}. {item}" for i, item in enumerate(items))

    async def execute(self, **inputs: Any) -> T:
        """
        Execute the agent with structured output.

        This method:
        1. Builds the prompt using the SOP template
        2. Invokes Gemini Model with structured output
        3. Parses and validates the response
        4. Tracks execution statistics

        Args:
            **inputs: Agent-specific inputs

        Returns:
            Structured output matching the output_schema
        """
        start_time = time.time()

        # Build the prompt from SOP template
        prompt = self._build_prompt(**inputs)

        # Get LLM configured for structured output
        llm = get_llm_with_structured_output(self.output_schema)

        # Create messages
        messages = [
            SystemMessage(content=self.sop.role),
            HumanMessage(content=prompt),
        ]

        # Execute and get structured response
        try:
            result = await llm.ainvoke(messages)

            # Track execution stats
            self._execution_stats = {
                "execution_time_ms": int((time.time() - start_time) * 1000),
                "status": "success",
                "agent_name": self.name,
            }

            return result

        except Exception as e:
            self._execution_stats = {
                "execution_time_ms": int((time.time() - start_time) * 1000),
                "status": "error",
                "error": str(e),
                "agent_name": self.name,
            }
            raise

    async def execute_raw(self, **inputs: Any) -> str:
        """
        Execute the agent and return raw text response.

        Useful for debugging or when structured output is not needed.

        Args:
            **inputs: Agent-specific inputs

        Returns:
            Raw text response from the LLM
        """
        prompt = self._build_prompt(**inputs)
        llm = get_llm()

        messages = [
            SystemMessage(content=self.sop.role),
            HumanMessage(content=prompt),
        ]

        response = await llm.ainvoke(messages)
        return response.content

    def get_execution_stats(self) -> dict[str, Any]:
        """Get statistics from the last execution."""
        return self._execution_stats.copy()

    def get_sop_summary(self) -> dict[str, Any]:
        """Get a summary of the agent's SOP for debugging."""
        return {
            "name": self.name,
            "role": self.sop.role[:100] + "...",
            "objective": self.sop.objective[:100] + "...",
            "num_constraints": len(self.sop.constraints),
            "num_quality_checks": len(self.sop.quality_checklist),
        }
