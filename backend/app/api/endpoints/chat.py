"""Chat endpoints for iterative project updates."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user
from app.models.user import User
from app.schemas.projects import ChatMessage, ChatRequest, ChatResponse
from app.services import ChatService, PipelineService

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


@router.post("/{project_id}", response_model=ChatResponse)
async def send_chat_message(
    project_id: str,
    request: ChatRequest,
    user: User = Depends(get_current_user),
) -> ChatResponse:
    """
    Send a chat message to update a project.
    """
    await _verify_project_owner(project_id, user)

    service = ChatService()

    try:
        response = await service.process_message(project_id, request)
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat message: {str(e)}",
        )


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
