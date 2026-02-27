"""
Engineer Agent - Code Generation

The Engineer Agent implements the system design by generating
complete, production-ready code files.

LLM: Gemini 3 (via LangChain)
"""

import json
from typing import Any

from app.agents.base import BaseAgent
from app.schemas.agents import ArchitectOutput, EngineerOutput, ManagerOutput
from app.sop import ENGINEER_SOP


class EngineerAgent(BaseAgent[EngineerOutput]):
    """
    Engineer Agent - Generates production-ready code.

    This agent produces:
    - Complete source code files
    - All necessary configuration files
    - Dependency specifications
    - Setup instructions
    """

    def __init__(self):
        """Initialize Engineer Agent with its SOP."""
        super().__init__(sop=ENGINEER_SOP, output_schema=EngineerOutput)

    @property
    def name(self) -> str:
        return "EngineerAgent"

    def _format_file_structure(self, architect_output: ArchitectOutput) -> str:
        """Format file structure for the prompt."""
        lines = []
        for file in architect_output.file_structure:
            deps = ", ".join(file.dependencies) if file.dependencies else "none"
            lines.append(f"- {file.path}")
            lines.append(f"  Purpose: {file.purpose}")
            lines.append(f"  Dependencies: {deps}")
        return "\n".join(lines) if lines else "No file structure defined."

    def _format_components(self, architect_output: ArchitectOutput) -> str:
        """Format components for the prompt."""
        lines = []
        for comp in architect_output.components:
            lines.append(f"\n### {comp.name} ({comp.type})")
            lines.append(f"Description: {comp.description}")
            lines.append(f"Technologies: {', '.join(comp.technologies)}")
            if comp.files:
                lines.append("Files:")
                for f in comp.files:
                    lines.append(f"  - {f.path}: {f.purpose}")
        return "\n".join(lines) if lines else "No components defined."

    def _format_requirements(self, manager_output: ManagerOutput) -> str:
        """Format requirements for reference."""
        lines = []
        for req in manager_output.requirements:
            lines.append(f"- [{req.priority}] {req.description}")
        return "\n".join(lines) if lines else "No requirements."

    def _build_prompt(self, **inputs: Any) -> str:
        """
        Build the Engineer Agent prompt.

        Args:
            architect_output: Output from the Architect Agent
            manager_output: Output from the Manager Agent (for reference)

        Returns:
            Formatted prompt for the LLM
        """
        architect_output: ArchitectOutput = inputs.get("architect_output")
        manager_output: ManagerOutput = inputs.get("manager_output")

        if not architect_output:
            raise ValueError("architect_output is required for EngineerAgent")
        if not manager_output:
            raise ValueError("manager_output is required for EngineerAgent")

        # Format SOP sections
        constraints_text = self._format_sop_section(self.sop.constraints)
        quality_text = self._format_sop_section(self.sop.quality_checklist)

        # Format architecture details
        file_structure = self._format_file_structure(architect_output)
        components = self._format_components(architect_output)
        requirements = self._format_requirements(manager_output)

        # Format API design
        api_design = json.dumps(architect_output.api_design, indent=2) if architect_output.api_design else "No API design."

        return f"""# Engineer Agent - Code Generation

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

## Project: {manager_output.project_name}
{manager_output.project_description}

## Architecture Type: {architect_output.architecture_type}

## Components:
{components}

## File Structure:
{file_structure}

## API Design:
{api_design}

## Data Flow:
{architect_output.data_flow}

---

## Original Requirements:
{requirements}

---

## Your Task
Implement ALL files listed in the file structure with production-ready code.

CRITICAL INSTRUCTIONS:
1. Generate COMPLETE file contents - no placeholders, no TODOs, no "// implement here"
2. Every file must be fully functional and runnable
3. Include all necessary imports at the top of each file
4. Add proper error handling throughout
5. Use consistent coding style and formatting
6. Add comments for complex logic
7. Ensure cross-file dependencies are correct

For each file, provide:
- file_path: The exact path as specified in the architecture
- file_content: Complete, working code
- file_language: The programming language or file type
- file_purpose: Brief description of the file's purpose

Generate your output as structured JSON with the files array containing all generated files."""


async def run_engineer_agent(
    architect_output: ArchitectOutput,
    manager_output: ManagerOutput,
) -> EngineerOutput:
    """
    Convenience function to run the Engineer Agent.

    Args:
        architect_output: Output from Architect Agent
        manager_output: Output from Manager Agent

    Returns:
        EngineerOutput with generated code files
    """
    agent = EngineerAgent()
    return await agent.execute(
        architect_output=architect_output,
        manager_output=manager_output,
    )
