"""
Chat Service - Handles iterative chat-based updates.

This service processes chat messages and determines which agents
need to be re-executed based on user intent.
"""

import uuid
from datetime import datetime
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.graph import AgentPipeline
from app.llm import get_llm
from app.schemas.agents import GeneratedFileSpec
from app.schemas.projects import ChatMessage, ChatRequest, ChatResponse, Project
from app.storage import FileStore, ProjectStore


# Prompt for intent classification
INTENT_CLASSIFIER_PROMPT = """You are an intent classifier for a code generation system.

Analyze the user's message and determine which agents need to be re-executed.
The agents are:
- manager: Handles requirements changes (new features, scope changes)
- architect: Handles structural changes (new files, architecture changes)
- engineer: Handles code changes (bug fixes, code modifications, style changes)
- qa: Handles test changes (new tests, test modifications)

User Message: {message}

Current Project Context:
- Name: {project_name}
- Description: {project_description}
- Files: {file_count} files generated

Respond with ONLY a JSON object containing:
{{
    "agents_to_run": ["engineer"],  // List of agents that need to run, in order
    "affected_files": ["path/to/file.ts"],  // Files likely to be affected
    "change_description": "Brief description of the change"
}}

Be conservative - only include agents that truly need to re-run.
For simple code changes, only "engineer" is needed.
For new features, you may need "manager" -> "architect" -> "engineer".
"""


class ChatService:
    """
    Service for handling chat-based project iterations.

    Analyzes user messages to determine which agents need re-execution
    and updates only the affected files.
    """

    def __init__(self):
        """Initialize the chat service."""
        self.project_store = ProjectStore()
        self.file_store = FileStore()
        self.pipeline = AgentPipeline()
        self.llm = get_llm(temperature=0.3)  # Lower temperature for classification

    async def process_message(
        self,
        project_id: str,
        request: ChatRequest,
    ) -> ChatResponse:
        """
        Process a chat message and update the project.

        Args:
            project_id: Project identifier
            request: Chat request with user message

        Returns:
            ChatResponse with assistant response and updates
        """
        project = await self.project_store.get(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        # Classify intent
        intent = await self._classify_intent(request.message, project)

        # Execute required agents
        agents_executed = []
        files_modified = []

        if intent.get("agents_to_run"):
            agents_executed, files_modified = await self._execute_agents(
                project_id,
                project,
                request.message,
                intent,
            )

        # Generate response message
        response_content = await self._generate_response(
            request.message,
            intent,
            files_modified,
        )

        # Create response
        response_message = ChatMessage(
            id=str(uuid.uuid4())[:8],
            role="assistant",
            content=response_content,
            timestamp=datetime.utcnow(),
            agent_triggered=agents_executed[0] if agents_executed else None,
            files_modified=files_modified,
        )

        return ChatResponse(
            message=response_message,
            agents_executed=agents_executed,
            files_modified=files_modified,
            project_updated=len(files_modified) > 0,
        )

    async def _classify_intent(
        self,
        message: str,
        project: Project,
    ) -> dict[str, Any]:
        """Classify the user's intent to determine which agents to run."""
        file_count = 0
        if project.state.engineer_output:
            file_count = len(project.state.engineer_output.files)

        prompt = INTENT_CLASSIFIER_PROMPT.format(
            message=message,
            project_name=project.name or "Unnamed",
            project_description=project.description or "No description",
            file_count=file_count,
        )

        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            content = response.content

            # Parse JSON from response
            import json
            import re

            # Extract JSON from the response
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())

            # Default to engineer only if parsing fails
            return {
                "agents_to_run": ["engineer"],
                "affected_files": [],
                "change_description": message,
            }

        except Exception:
            # Default fallback
            return {
                "agents_to_run": ["engineer"],
                "affected_files": [],
                "change_description": message,
            }

    async def _execute_agents(
        self,
        project_id: str,
        project: Project,
        message: str,
        intent: dict[str, Any],
    ) -> tuple[list[str], list[str]]:
        """Execute the required agents and return results."""
        agents_to_run = intent.get("agents_to_run", [])
        affected_files = intent.get("affected_files", [])
        change_description = intent.get("change_description", message)

        if not agents_to_run:
            return [], []

        # Build context for the change
        context = f"""
This is an INCREMENTAL UPDATE to an existing project.

Change Request: {message}
Change Description: {change_description}
Affected Files: {', '.join(affected_files) if affected_files else 'To be determined'}

IMPORTANT: Only modify what's necessary. Do not regenerate the entire project.
Focus on the specific change requested.
"""

        # Determine starting point
        start_agent = agents_to_run[0]

        # Get current state
        from app.graph.state import PipelineState

        current_state: PipelineState = {
            "project_id": project_id,
            "user_prompt": project.prompt + "\n\n" + context,
            "context": context,
            "manager_output": project.state.manager_output,
            "architect_output": project.state.architect_output,
            "engineer_output": project.state.engineer_output,
            "qa_output": project.state.qa_output,
            "current_stage": "pending",
            "progress": 0,
            "error": None,
            "error_stage": None,
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "execution_log": [],
        }

        # Resume from the starting agent
        final_state = await self.pipeline.resume_from(current_state, start_agent)

        # Get modified files
        files_modified = []
        if final_state.get("engineer_output"):
            for file_spec in final_state["engineer_output"].files:
                await self.file_store.write_file(project_id, file_spec)
                files_modified.append(file_spec.file_path)

        # Update project state
        await self.project_store.update_state(
            project_id,
            manager_output=final_state.get("manager_output") or project.state.manager_output,
            architect_output=final_state.get("architect_output") or project.state.architect_output,
            engineer_output=final_state.get("engineer_output") or project.state.engineer_output,
            qa_output=final_state.get("qa_output") or project.state.qa_output,
        )

        return agents_to_run, files_modified

    async def _generate_response(
        self,
        user_message: str,
        intent: dict[str, Any],
        files_modified: list[str],
    ) -> str:
        """Generate a natural language response for the user."""
        agents_run = intent.get("agents_to_run", [])
        change_desc = intent.get("change_description", "")

        if not agents_run:
            return "I understood your message, but no changes were needed."

        if files_modified:
            files_list = "\n".join(f"- {f}" for f in files_modified[:5])
            if len(files_modified) > 5:
                files_list += f"\n- ... and {len(files_modified) - 5} more files"

            return f"""I've processed your request: {change_desc}

The following files were updated:
{files_list}

You can view the changes in the file explorer."""

        return f"""I've analyzed your request: {change_desc}

The {', '.join(agents_run)} agent(s) have been executed to process your changes."""

    async def get_chat_history(
        self,
        project_id: str,
        limit: int = 50,
    ) -> list[ChatMessage]:
        """
        Get chat history for a project.

        Note: This is a simplified implementation.
        A production system would store chat history in the database.
        """
        # For now, return empty - would need chat storage
        return []
