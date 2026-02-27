"""
Manager Agent - Requirements Analysis

The Manager Agent is the first agent in the pipeline.
It transforms natural language user prompts into structured requirements.

LLM: Gemini Model (via LangChain)
"""

from typing import Any

from app.agents.base import BaseAgent
from app.schemas.agents import ManagerOutput
from app.sop import MANAGER_SOP


class ManagerAgent(BaseAgent[ManagerOutput]):
    """
    Manager Agent - Converts user prompts to structured requirements.

    This agent analyzes natural language prompts and produces:
    - Project name and description
    - Project type classification
    - Technology stack recommendations
    - Structured requirements with priorities
    - Constraints and assumptions
    """

    def __init__(self):
        """Initialize Manager Agent with its SOP."""
        super().__init__(sop=MANAGER_SOP, output_schema=ManagerOutput)

    @property
    def name(self) -> str:
        return "ManagerAgent"

    def _build_prompt(self, **inputs: Any) -> str:
        """
        Build the Manager Agent prompt.

        Args:
            user_prompt: The user's natural language request
            context: Optional additional context

        Returns:
            Formatted prompt for the LLM
        """
        user_prompt = inputs.get("user_prompt", "")
        context = inputs.get("context", "No additional context provided.")

        # Format constraints and quality checklist
        constraints_text = self._format_sop_section(self.sop.constraints)
        quality_text = self._format_sop_section(self.sop.quality_checklist)

        return self.sop.prompt_template.format(
            role=self.sop.role,
            objective=self.sop.objective,
            constraints=constraints_text,
            quality_checklist=quality_text,
            user_prompt=user_prompt,
            context=context,
        )


async def run_manager_agent(user_prompt: str, context: str = "") -> ManagerOutput:
    """
    Convenience function to run the Manager Agent.

    Args:
        user_prompt: User's natural language request
        context: Optional additional context

    Returns:
        ManagerOutput with structured requirements
    """
    agent = ManagerAgent()
    return await agent.execute(user_prompt=user_prompt, context=context)
