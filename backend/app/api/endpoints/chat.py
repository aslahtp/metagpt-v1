"""Chat endpoints for iterative project updates.

The main POST /{project_id} endpoint uses Server-Sent Events (SSE) so that
the response stream keeps the Cloud Run HTTP connection alive while the LLM
processes the request (which can take 30–120 s for large projects).

SSE event types emitted:
  thinking  — keepalive heartbeats while work is in progress
  done      — final ChatResponse payload (JSON)
  error     — error message (string)
"""

import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sse_starlette.sse import EventSourceResponse

from app.auth import get_current_user
from app.models.user import User
from app.schemas.projects import ChatRequest, ChatResponse
from app.services import ChatService, PipelineService

logger = logging.getLogger(__name__)

router = APIRouter()


async def _verify_project_owner(project_id: str, user: User):
    """Verify the project exists and belongs to the user."""
    service = PipelineService()
    project = await service.get_project(project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    if project.user_id != str(user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this project",
        )

    return project


@router.post("/{project_id}")
async def send_chat_message(
    project_id: str,
    request: ChatRequest,
    user: User = Depends(get_current_user),
):
    """
    Send a chat message and stream the response via SSE.

    The endpoint returns a ``text/event-stream`` response that emits:
    - ``event: thinking`` — periodic keepalive during LLM processing
    - ``event: done``     — the full ``ChatResponse`` JSON when complete
    - ``event: error``    — error detail string on failure

    This avoids Cloud Run's 30 s HTTP request timeout by keeping the
    connection alive with heartbeat events while the LLM generates.
    """
    await _verify_project_owner(project_id, user)

    async def event_generator():
        import asyncio

        service = ChatService()

        logger.info(
            "Chat SSE stream started for project %s: %s",
            project_id,
            request.message[:80],
        )

        # Run the blocking chat work as an asyncio task so we can send
        # keepalive events while it's in-progress.
        task = asyncio.create_task(
            service.process_message(project_id, request)
        )

        # Send a keepalive heartbeat every 10 s while the task runs.
        # SSE over HTTP/1.1 through Cloud Run / nginx proxies will drop
        # idle connections; frequent small frames prevent that.
        heartbeat_interval = 10
        elapsed = 0
        while not task.done():
            await asyncio.sleep(1)
            elapsed += 1
            if elapsed % heartbeat_interval == 0:
                yield {
                    "event": "thinking",
                    "data": json.dumps({"elapsed_s": elapsed}),
                }

        # Task finished — check for exception
        exc = task.exception()
        if exc is not None:
            logger.error(
                "Chat task failed for project %s: %s", project_id, exc
            )
            detail = str(exc)
            yield {
                "event": "error",
                "data": json.dumps({"detail": detail}),
            }
            return

        response: ChatResponse = task.result()
        logger.info(
            "Chat SSE done for project %s: %d files modified",
            project_id,
            len(response.files_modified),
        )
        yield {
            "event": "done",
            "data": response.model_dump_json(),
        }

    return EventSourceResponse(event_generator())


@router.get("/{project_id}/history")
async def get_chat_history(
    project_id: str,
    limit: int = 50,
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get chat history for a project.
    """
    await _verify_project_owner(project_id, user)

    service = ChatService()

    try:
        history = await service.get_chat_history(project_id, limit)
        return {
            "project_id": project_id,
            "messages": [m.model_dump() for m in history],
            "total": len(history),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/{project_id}/suggest")
async def get_suggestions(
    project_id: str,
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get AI-powered suggestions for what to do next.
    """
    project = await _verify_project_owner(project_id, user)

    suggestions = []

    if project.state.qa_output:
        qa = project.state.qa_output

        if qa.approval_status == "needs-revision":
            for note in qa.validation_notes[:3]:
                if note.severity in ["error", "warning"]:
                    suggestions.append({
                        "type": "fix",
                        "priority": "high" if note.severity == "error" else "medium",
                        "description": note.description,
                        "action": note.recommendation,
                    })

        if "low" in qa.test_coverage_estimate.lower():
            suggestions.append({
                "type": "enhancement",
                "priority": "medium",
                "description": "Test coverage could be improved",
                "action": "Add more unit tests for critical components",
            })

    if not suggestions:
        suggestions = [
            {
                "type": "enhancement",
                "priority": "low",
                "description": "Add documentation",
                "action": "Ask me to add README or API documentation",
            },
            {
                "type": "enhancement",
                "priority": "low",
                "description": "Add error handling",
                "action": "Ask me to improve error handling and edge cases",
            },
        ]

    return {
        "project_id": project_id,
        "suggestions": suggestions,
    }
