"""
MetaGPT: Main FastAPI Application

A production-ready agentic system with SOP-driven autonomous agents.
Uses Google Gemini Model via LangChain for all agent operations.
"""

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.config import get_settings
from app.llm.gemini import get_llm_config

# Only show HTTP request/response logs + app-level logs
logging.basicConfig(level=logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.INFO)
logging.getLogger("app").setLevel(logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    settings = get_settings()
    print(f"Starting {settings.app_name} v{settings.app_version}")
    print(f"LLM Configuration: {get_llm_config()}")

    # Initialize MongoDB
    from app.db import init_db

    await init_db()

    yield

    # Shutdown
    print("Shutting down...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="""
        MetaGPT: An agentic code generation system.

        This system uses SOP-driven autonomous agents to transform natural language
        prompts into fully functional codebases.

        ## Agent Pipeline

        The system follows a strict workflow:
        1. **Manager Agent**: Converts prompts to structured requirements
        2. **Architect Agent**: Designs system architecture
        3. **Engineer Agent**: Generates production-ready code
        4. **QA Agent**: Creates tests and validates quality

        ## LLM

        All agents use **Google Gemini Model** via LangChain.
        """,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(api_router, prefix=settings.api_prefix)

    # Health check
    @app.get("/health")
    async def health_check() -> dict[str, Any]:
        """Health check endpoint."""
        return {
            "status": "healthy",
            "app": settings.app_name,
            "version": settings.app_version,
            "llm": get_llm_config(),
        }

    # Root redirect
    @app.get("/")
    async def root() -> dict[str, str]:
        """Root endpoint with API info."""
        return {
            "message": f"Welcome to {settings.app_name}",
            "docs": "/docs",
            "health": "/health",
            "api": settings.api_prefix,
        }

    return app


# Create the app instance
app = create_app()


def serve() -> None:
    """Entry point for `uv run serve`. Avoids Windows 'Failed to canonicalize script path'."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )


if __name__ == "__main__":
    serve()
