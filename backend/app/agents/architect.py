"""
Architect Agent - System Design

The Architect Agent receives requirements from the Manager and designs
the complete system architecture including file structure and APIs.

LLM: Gemini 3 Flash (via LangChain)
"""

import json
from typing import Any

from app.agents.base import BaseAgent
from app.schemas.agents import ArchitectOutput, ManagerOutput
from app.sop import ARCHITECT_SOP


class ArchitectAgent(BaseAgent[ArchitectOutput]):
    """
    Architect Agent - Designs system architecture from requirements.

    This agent produces:
    - Architecture pattern selection
    - Component breakdown
    - Complete file structure
    - API design
    - Database schema
    - Data flow description
    """

    def __init__(self):
        """Initialize Architect Agent with its SOP."""
        super().__init__(sop=ARCHITECT_SOP, output_schema=ArchitectOutput)

    @property
    def name(self) -> str:
        return "ArchitectAgent"

    def _format_requirements(self, manager_output: ManagerOutput) -> str:
        """Format requirements for the prompt."""
        lines = []
        for req in manager_output.requirements:
            lines.append(
                f"- [{req.id}] ({req.priority}) {req.category}: {req.description}"
            )
            if req.acceptance_criteria:
                for criterion in req.acceptance_criteria:
                    lines.append(f"  - Criterion: {criterion}")
        return "\n".join(lines) if lines else "No specific requirements provided."

    def _build_prompt(self, **inputs: Any) -> str:
        """
        Build the Architect Agent prompt.

        Args:
            manager_output: Output from the Manager Agent

        Returns:
            Formatted prompt for the LLM
        """
        manager_output: ManagerOutput = inputs.get("manager_output")

        if not manager_output:
            raise ValueError("manager_output is required for ArchitectAgent")

        # Format constraints and quality checklist
        constraints_text = self._format_sop_section(self.sop.constraints)
        quality_text = self._format_sop_section(self.sop.quality_checklist)

        # Format requirements
        requirements_text = self._format_requirements(manager_output)

        # Format constraints from manager
        constraints_list = "\n".join(
            f"- {c}" for c in manager_output.constraints
        ) if manager_output.constraints else "No specific constraints."

        # Format tech stack
        tech_stack = ", ".join(manager_output.tech_stack) if manager_output.tech_stack else "Not specified"

        return f"""# Architect Agent - System Design

## Your Role
{self.sop.role}

## Your Objective
{self.sop.objective}

## Constraints
{constraints_text}

## Quality Checklist
Before finalizing your output, verify:
{quality_text}

---

## Input from Manager Agent
### Project: {manager_output.project_name}
### Description: {manager_output.project_description}
### Type: {manager_output.project_type}
### Tech Stack: {tech_stack}

### Requirements:
{requirements_text}

### Constraints:
{constraints_list}

### Assumptions:
{chr(10).join('- ' + a for a in manager_output.assumptions) if manager_output.assumptions else 'None stated.'}

---

## Your Task
Design the complete system architecture for this project.

Think step by step:
1. What architectural pattern best fits these requirements?
2. What are the major components needed?
3. What files need to be created?
4. How will data flow through the system?
5. What APIs need to be exposed?
6. What database structure is needed (if any)?

Provide your complete design as structured JSON output."""


async def run_architect_agent(manager_output: ManagerOutput) -> ArchitectOutput:
    """
    Convenience function to run the Architect Agent.

    Args:
        manager_output: Output from Manager Agent

    Returns:
        ArchitectOutput with system design
    """
    agent = ArchitectAgent()
    return await agent.execute(manager_output=manager_output)
