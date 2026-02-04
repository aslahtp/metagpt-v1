"""
QA Agent - Quality Assurance & Testing

The QA Agent reviews generated code, creates test cases,
and provides quality validation for the entire project.

LLM: Gemini 3 Flash (via LangChain)
"""

import json
from typing import Any

from app.agents.base import BaseAgent
from app.schemas.agents import (
    ArchitectOutput,
    EngineerOutput,
    ManagerOutput,
    QAOutput,
)
from app.sop import QA_SOP


class QAAgent(BaseAgent[QAOutput]):
    """
    QA Agent - Validates code and creates test cases.

    This agent produces:
    - Comprehensive test cases
    - Code review findings
    - Security and performance notes
    - Quality score and approval status
    """

    def __init__(self):
        """Initialize QA Agent with its SOP."""
        super().__init__(sop=QA_SOP, output_schema=QAOutput)

    @property
    def name(self) -> str:
        return "QAAgent"

    def _format_files(self, engineer_output: EngineerOutput) -> str:
        """Format generated files for review."""
        lines = []
        for file in engineer_output.files:
            lines.append(f"\n### File: {file.file_path}")
            lines.append(f"Language: {file.file_language}")
            lines.append(f"Purpose: {file.file_purpose}")
            lines.append("```")
            # Truncate very long files for the prompt
            content = file.file_content
            if len(content) > 3000:
                content = content[:2500] + "\n\n... [TRUNCATED] ...\n\n" + content[-500:]
            lines.append(content)
            lines.append("```")
        return "\n".join(lines)

    def _format_requirements(self, manager_output: ManagerOutput) -> str:
        """Format requirements for validation."""
        lines = []
        for req in manager_output.requirements:
            lines.append(f"- [{req.id}] {req.description}")
            for criterion in req.acceptance_criteria:
                lines.append(f"  - Acceptance: {criterion}")
        return "\n".join(lines) if lines else "No requirements."

    def _format_architecture(self, architect_output: ArchitectOutput) -> str:
        """Format architecture summary."""
        lines = [
            f"Architecture: {architect_output.architecture_type}",
            f"Components: {len(architect_output.components)}",
            f"Files: {len(architect_output.file_structure)}",
        ]
        if architect_output.api_design:
            lines.append(f"API Endpoints: {len(architect_output.api_design)}")
        return "\n".join(lines)

    def _build_prompt(self, **inputs: Any) -> str:
        """
        Build the QA Agent prompt.

        Args:
            engineer_output: Output from the Engineer Agent
            architect_output: Output from the Architect Agent
            manager_output: Output from the Manager Agent

        Returns:
            Formatted prompt for the LLM
        """
        engineer_output: EngineerOutput = inputs.get("engineer_output")
        architect_output: ArchitectOutput = inputs.get("architect_output")
        manager_output: ManagerOutput = inputs.get("manager_output")

        if not engineer_output:
            raise ValueError("engineer_output is required for QAAgent")
        if not architect_output:
            raise ValueError("architect_output is required for QAAgent")
        if not manager_output:
            raise ValueError("manager_output is required for QAAgent")

        # Format SOP sections
        constraints_text = self._format_sop_section(self.sop.constraints)
        quality_text = self._format_sop_section(self.sop.quality_checklist)

        # Format inputs
        files_text = self._format_files(engineer_output)
        requirements_text = self._format_requirements(manager_output)
        architecture_text = self._format_architecture(architect_output)

        return f"""# QA Agent - Quality Assurance & Testing

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

## Architecture Summary:
{architecture_text}

## Original Requirements:
{requirements_text}

---

## Generated Files for Review:
{files_text}

## Implementation Notes from Engineer:
{engineer_output.implementation_notes}

## Dependencies:
{', '.join(engineer_output.dependencies_added) if engineer_output.dependencies_added else 'None listed'}

---

## Your Task
Perform comprehensive QA review:

1. **Test Case Creation**
   - Create test cases for all major functionality
   - Include unit tests, integration tests, and E2E tests where applicable
   - Specify test type, steps, and expected results

2. **Code Review**
   - Check for syntax errors and logical issues
   - Identify security vulnerabilities
   - Note performance concerns
   - Verify coding standards compliance

3. **Requirements Validation**
   - Verify each requirement is addressed
   - Check acceptance criteria can be met
   - Identify any gaps

4. **Quality Assessment**
   - Assign a quality score (0-100)
   - Provide approval status: approved, needs-revision, or rejected
   - Justify your assessment

Generate your complete QA analysis as structured JSON output."""


async def run_qa_agent(
    engineer_output: EngineerOutput,
    architect_output: ArchitectOutput,
    manager_output: ManagerOutput,
) -> QAOutput:
    """
    Convenience function to run the QA Agent.

    Args:
        engineer_output: Output from Engineer Agent
        architect_output: Output from Architect Agent
        manager_output: Output from Manager Agent

    Returns:
        QAOutput with test cases and validation
    """
    agent = QAAgent()
    return await agent.execute(
        engineer_output=engineer_output,
        architect_output=architect_output,
        manager_output=manager_output,
    )
