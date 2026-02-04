"""API endpoint tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "llm" in data


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "docs" in data


@pytest.mark.asyncio
async def test_create_project(client: AsyncClient, sample_prompt: str):
    """Test project creation (without pipeline execution)."""
    response = await client.post(
        "/api/v1/projects",
        json={"prompt": sample_prompt},
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["prompt"] == sample_prompt


@pytest.mark.asyncio
async def test_list_projects(client: AsyncClient):
    """Test listing projects."""
    response = await client.get("/api/v1/projects")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_nonexistent_project(client: AsyncClient):
    """Test getting a project that doesn't exist."""
    response = await client.get("/api/v1/projects/nonexistent")
    assert response.status_code == 404
