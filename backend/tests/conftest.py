"""Pytest configuration and fixtures."""

import os
import pytest
from httpx import AsyncClient

# Set test environment
os.environ["GOOGLE_API_KEY"] = "test-api-key"
os.environ["PROJECTS_DIR"] = "./test_projects"
os.environ["DEBUG"] = "true"


@pytest.fixture
def anyio_backend():
    """Use asyncio backend for async tests."""
    return "asyncio"


@pytest.fixture
async def client():
    """Create async test client."""
    from app.main import app

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_prompt():
    """Sample user prompt for testing."""
    return "Build a simple todo app with React and a REST API backend."


@pytest.fixture
def sample_manager_output():
    """Sample Manager agent output."""
    from app.schemas.agents import ManagerOutput, Requirement

    return ManagerOutput(
        project_name="todo-app",
        project_description="A simple todo application",
        project_type="web-app",
        tech_stack=["React", "Node.js", "Express"],
        requirements=[
            Requirement(
                id="REQ-001",
                category="functional",
                description="User can create todo items",
                priority="high",
                acceptance_criteria=["Todo form exists", "Submit creates todo"],
            ),
        ],
        constraints=["Must be responsive"],
        assumptions=["Single user application"],
        reasoning="This is a simple CRUD application...",
    )
