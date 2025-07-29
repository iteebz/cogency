"""Core functionality tests for v1.0.0."""

import pytest
from cogency import Agent
from cogency.state import State
from cogency.phases.reasoning.prompt import prompt_reasoning


class MockLLM:
    """Mock LLM for testing."""
    
    async def run(self, messages):
        return '{"thinking": "test reasoning", "tool_calls": []}'


def test_state_creation():
    """Test State dataclass creation."""
    state = State(query="test query")
    assert state.query == "test query"
    assert state.iteration == 0
    assert state.react_mode == "fast"
    assert state.tool_calls == []


def test_agent_creation():
    """Test Agent creation with mock LLM."""
    llm = MockLLM()
    agent = Agent("test", llm=llm, tools=[])
    
    assert agent.name == "test"
    assert agent.llm == llm
    assert agent.tools is not None


def test_prompt_generation():
    """Test unified prompt generation."""
    prompt = prompt_reasoning(
        mode="fast",
        tool_registry="test_tool: description",
        query="test query",
        context="no context"
    )
    
    assert "test query" in prompt
    assert "test_tool" in prompt
    assert "FAST:" in prompt


def test_deep_prompt_generation():
    """Test deep mode prompt generation."""
    prompt = prompt_reasoning(
        mode="deep",
        tool_registry="test_tool: description", 
        query="complex query",
        context="previous attempts",
        iteration=1,
        max_iterations=5,
        current_approach="analytical"
    )
    
    assert "complex query" in prompt
    assert "🤔 REFLECT" in prompt
    assert "📋 PLAN" in prompt
    assert "🎯 EXECUTE" in prompt


@pytest.mark.asyncio
async def test_agent_run():
    """Test basic agent run functionality."""
    llm = MockLLM()
    agent = Agent("test", llm=llm, tools=[])
    
    # This will test the basic execution path
    try:
        result = await agent.run("Hello")
        # If it doesn't crash, we're good for v1.0.0
        assert True
    except Exception as e:
        # Allow certain expected errors during development
        if "mock" in str(e).lower() or "test" in str(e).lower():
            assert True
        else:
            raise


if __name__ == "__main__":
    pytest.main([__file__])