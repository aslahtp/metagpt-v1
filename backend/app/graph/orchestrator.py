"""
LangGraph Orchestrator - Deterministic Agent Pipeline.

This module implements the core agent orchestration using LangGraph.
The pipeline follows a strict linear flow:
    User → Manager → Architect → Engineer → QA

Key features:
- Deterministic routing (no agent autonomy loops)
- State persistence after each node
- Support for re-entry from chat
- Streaming support for real-time updates
"""

import asyncio
from datetime import datetime
from typing import Any, AsyncGenerator, Callable

from langgraph.graph import END, StateGraph

from app.agents import ArchitectAgent, EngineerAgent, ManagerAgent, QAAgent
from app.graph.state import PipelineState, create_initial_state


class AgentPipeline:
    """
    LangGraph-based agent pipeline orchestrator.

    Implements the deterministic workflow:
    Manager → Architect → Engineer → QA

    All agents use Gemini 3 Flash as configured in the llm module.
    """

    def __init__(self):
        """Initialize the pipeline with the state graph."""
        self.graph = self._build_graph()
        self._state_callbacks: list[Callable[[PipelineState], None]] = []

    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph state graph with all agent nodes.

        Returns:
            Compiled StateGraph ready for execution
        """
        # Create the state graph
        workflow = StateGraph(PipelineState)

        # Add nodes for each agent
        workflow.add_node("manager", self._run_manager)
        workflow.add_node("architect", self._run_architect)
        workflow.add_node("engineer", self._run_engineer)
        workflow.add_node("qa", self._run_qa)

        # Set entry point
        workflow.set_entry_point("manager")

        # Define edges (linear flow)
        workflow.add_edge("manager", "architect")
        workflow.add_edge("architect", "engineer")
        workflow.add_edge("engineer", "qa")
        workflow.add_edge("qa", END)

        # Compile the graph
        return workflow.compile()

    async def _run_manager(self, state: PipelineState) -> dict[str, Any]:
        """Execute Manager Agent node."""
        self._log_execution(state, "manager", "started")

        try:
            agent = ManagerAgent()
            output = await agent.execute(
                user_prompt=state["user_prompt"],
                context=state.get("context", ""),
            )

            self._log_execution(state, "manager", "completed", agent.get_execution_stats())

            return {
                "manager_output": output,
                "current_stage": "manager",
                "progress": 25.0,
            }

        except Exception as e:
            self._log_execution(state, "manager", "error", {"error": str(e)})
            return {
                "error": str(e),
                "error_stage": "manager",
                "current_stage": "error",
            }

    async def _run_architect(self, state: PipelineState) -> dict[str, Any]:
        """Execute Architect Agent node."""
        self._log_execution(state, "architect", "started")

        # Check for previous stage error
        if state.get("error"):
            return {}

        try:
            agent = ArchitectAgent()
            output = await agent.execute(
                manager_output=state["manager_output"],
            )

            self._log_execution(state, "architect", "completed", agent.get_execution_stats())

            return {
                "architect_output": output,
                "current_stage": "architect",
                "progress": 50.0,
            }

        except Exception as e:
            self._log_execution(state, "architect", "error", {"error": str(e)})
            return {
                "error": str(e),
                "error_stage": "architect",
                "current_stage": "error",
            }

    async def _run_engineer(self, state: PipelineState) -> dict[str, Any]:
        """Execute Engineer Agent node."""
        self._log_execution(state, "engineer", "started")

        if state.get("error"):
            return {}

        try:
            agent = EngineerAgent()
            output = await agent.execute(
                architect_output=state["architect_output"],
                manager_output=state["manager_output"],
            )

            self._log_execution(state, "engineer", "completed", agent.get_execution_stats())

            return {
                "engineer_output": output,
                "current_stage": "engineer",
                "progress": 75.0,
            }

        except Exception as e:
            self._log_execution(state, "engineer", "error", {"error": str(e)})
            return {
                "error": str(e),
                "error_stage": "engineer",
                "current_stage": "error",
            }

    async def _run_qa(self, state: PipelineState) -> dict[str, Any]:
        """Execute QA Agent node."""
        self._log_execution(state, "qa", "started")

        if state.get("error"):
            return {}

        try:
            agent = QAAgent()
            output = await agent.execute(
                engineer_output=state["engineer_output"],
                architect_output=state["architect_output"],
                manager_output=state["manager_output"],
            )

            self._log_execution(state, "qa", "completed", agent.get_execution_stats())

            return {
                "qa_output": output,
                "current_stage": "completed",
                "progress": 100.0,
                "completed_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            self._log_execution(state, "qa", "error", {"error": str(e)})
            return {
                "error": str(e),
                "error_stage": "qa",
                "current_stage": "error",
            }

    def _log_execution(
        self,
        state: PipelineState,
        agent: str,
        status: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Add entry to execution log."""
        log_entry = {
            "agent": agent,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
        }
        if details:
            log_entry["details"] = details

        # Append to execution log
        if "execution_log" not in state:
            state["execution_log"] = []
        state["execution_log"].append(log_entry)

    async def run(
        self,
        project_id: str,
        user_prompt: str,
        context: str = "",
    ) -> PipelineState:
        """
        Run the complete pipeline.

        Args:
            project_id: Unique project identifier
            user_prompt: User's natural language prompt
            context: Optional additional context

        Returns:
            Final pipeline state with all agent outputs
        """
        initial_state = create_initial_state(project_id, user_prompt, context)

        # Run the graph
        final_state = await self.graph.ainvoke(initial_state)

        return final_state

    async def stream(
        self,
        project_id: str,
        user_prompt: str,
        context: str = "",
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Stream pipeline execution with real-time updates.

        Args:
            project_id: Unique project identifier
            user_prompt: User's natural language prompt
            context: Optional additional context

        Yields:
            State updates after each agent execution
        """
        initial_state = create_initial_state(project_id, user_prompt, context)

        # Stream through the graph
        async for event in self.graph.astream(initial_state):
            # Extract the node name and state update
            for node_name, state_update in event.items():
                yield {
                    "node": node_name,
                    "update": state_update,
                    "timestamp": datetime.utcnow().isoformat(),
                }

    async def resume_from(
        self,
        state: PipelineState,
        start_from: str,
    ) -> PipelineState:
        """
        Resume pipeline execution from a specific stage.

        Useful for chat-based iterations where only certain agents
        need to be re-run.

        Args:
            state: Existing pipeline state
            start_from: Agent to start from (manager, architect, engineer, qa)

        Returns:
            Updated pipeline state
        """
        # Build a partial graph starting from the specified node
        partial_workflow = StateGraph(PipelineState)

        nodes = ["manager", "architect", "engineer", "qa"]
        start_idx = nodes.index(start_from)

        # Add only the nodes from start_from onwards
        node_funcs = {
            "manager": self._run_manager,
            "architect": self._run_architect,
            "engineer": self._run_engineer,
            "qa": self._run_qa,
        }

        for node in nodes[start_idx:]:
            partial_workflow.add_node(node, node_funcs[node])

        # Set entry and edges
        partial_workflow.set_entry_point(start_from)

        for i in range(start_idx, len(nodes) - 1):
            partial_workflow.add_edge(nodes[i], nodes[i + 1])

        partial_workflow.add_edge(nodes[-1], END)

        # Compile and run
        compiled = partial_workflow.compile()
        return await compiled.ainvoke(state)


def create_pipeline() -> AgentPipeline:
    """Create a new agent pipeline instance."""
    return AgentPipeline()


async def run_pipeline(
    project_id: str,
    user_prompt: str,
    context: str = "",
) -> PipelineState:
    """
    Convenience function to run the full pipeline.

    Args:
        project_id: Unique project identifier
        user_prompt: User's natural language prompt
        context: Optional additional context

    Returns:
        Final pipeline state
    """
    pipeline = create_pipeline()
    return await pipeline.run(project_id, user_prompt, context)
