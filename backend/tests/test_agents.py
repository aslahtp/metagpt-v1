"""Agent unit tests."""

import pytest

from app.agents import ManagerAgent, ArchitectAgent, EngineerAgent, QAAgent
from app.sop import get_agent_sop


def test_manager_agent_init():
    """Test Manager agent initialization."""
    agent = ManagerAgent()
    assert agent.name == "ManagerAgent"
    assert agent.sop is not None


def test_architect_agent_init():
    """Test Architect agent initialization."""
    agent = ArchitectAgent()
    assert agent.name == "ArchitectAgent"
    assert agent.sop is not None


def test_engineer_agent_init():
    """Test Engineer agent initialization."""
    agent = EngineerAgent()
    assert agent.name == "EngineerAgent"
    assert agent.sop is not None


def test_qa_agent_init():
    """Test QA agent initialization."""
    agent = QAAgent()
    assert agent.name == "QAAgent"
    assert agent.sop is not None


def test_get_agent_sop():
    """Test SOP retrieval for all agents."""
    for agent_name in ["manager", "architect", "engineer", "qa"]:
        sop = get_agent_sop(agent_name)
        assert sop is not None
        assert sop.role is not None
        assert sop.objective is not None
        assert len(sop.constraints) > 0
        assert len(sop.quality_checklist) > 0


def test_get_invalid_agent_sop():
    """Test SOP retrieval for invalid agent."""
    with pytest.raises(ValueError):
        get_agent_sop("invalid_agent")


def test_manager_agent_prompt_building(sample_prompt: str):
    """Test Manager agent prompt building."""
    agent = ManagerAgent()
    prompt = agent._build_prompt(user_prompt=sample_prompt, context="Test context")
    assert sample_prompt in prompt
    assert "Manager Agent" in prompt
    assert "Requirements Analysis" in prompt
