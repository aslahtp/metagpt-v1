"""Chat endpoints for iterative project updates."""

from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.schemas.projects import ChatMessage, ChatRequest, ChatResponse
from app.services import ChatService

router = APIRouter()


@router.post("/{project_id}", response_model=ChatResponse)
async def send_chat_message(
    project_id: str,
    request: ChatRequest,
) -> ChatResponse:
    """
    Send a chat message to update a project.

    This endpoint processes user messages and determines which agents
    need to be re-executed to fulfill the request.

    The system will:
    1. Analyze the message to classify intent
    2. Determine which agents need to run
    3. Execute the required agents
    4. Update only the affected files

    This enables incremental updates without regenerating the entire project.
    """
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
) -> dict[str, Any]:
    """
    Get chat history for a project.

    Returns the list of chat messages exchanged for this project.
    """
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
) -> dict[str, Any]:
    """
    Get AI-powered suggestions for what to do next.

    Based on the current project state, suggests possible improvements
    or next steps.
    """
    from app.services import PipelineService

    pipeline_service = PipelineService()
    project = await pipeline_service.get_project(project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    # Generate suggestions based on project state
    suggestions = []

    if project.state.qa_output:
        qa = project.state.qa_output

        # Suggest based on QA findings
        if qa.approval_status == "needs-revision":
            for note in qa.validation_notes[:3]:
                if note.severity in ["error", "warning"]:
                    suggestions.append({
                        "type": "fix",
                        "priority": "high" if note.severity == "error" else "medium",
                        "description": note.description,
                        "action": note.recommendation,
                    })

        # Suggest adding tests if coverage is low
        if "low" in qa.test_coverage_estimate.lower():
            suggestions.append({
                "type": "enhancement",
                "priority": "medium",
                "description": "Test coverage could be improved",
                "action": "Add more unit tests for critical components",
            })

    # Default suggestions if none from QA
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
