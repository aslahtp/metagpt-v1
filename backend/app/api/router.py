"""API router combining all endpoint modules."""

from fastapi import APIRouter

from app.api.endpoints import auth, chat, files, pipeline, projects

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(pipeline.router, prefix="/pipeline", tags=["pipeline"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
