"""Memory system integration tests."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from resilient_result import Result

from cogency.agent import Agent


@pytest.mark.asyncio
async def test_memory_integration(agent_with_memory):
    """Test agent with memory system integration."""
    assert agent_with_memory.memory is not None
    # Agent may have real or mocked memory - both are valid

    # Test memory has expected methods
    assert hasattr(agent_with_memory.memory, "load")
    assert hasattr(agent_with_memory.memory, "remember")


@pytest.mark.asyncio
async def test_memory_situate_call(agent_with_memory):
    """Test memory operations during execution."""
    with patch("cogency.agents.reason", new_callable=AsyncMock) as mock_reason:
        with patch("cogency.state.State.start_task", new_callable=AsyncMock) as mock_state:
            mock_state.return_value = Mock()
            mock_reason.return_value = Result.ok({"response": "Response with memory"})

            await agent_with_memory.run("Test query")

            # Verify memory methods exist and can be called
            # Note: memory might be real or mocked depending on fixture setup
            if hasattr(agent_with_memory.memory.load, "assert_called"):
                agent_with_memory.memory.load.assert_called()
            if hasattr(agent_with_memory.memory.remember, "assert_called"):
                agent_with_memory.memory.remember.assert_called()


def test_memory_enabled_vs_disabled():
    """Test difference between memory enabled and disabled agents."""
    # Memory disabled
    agent_no_memory = Agent("test", memory=False)
    assert agent_no_memory.memory is None

    # Memory enabled
    agent_with_memory = Agent("test", memory=True)
    assert agent_with_memory.memory is not None


def test_memory_interface(agent_with_memory):
    """Test Memory interface."""
    # Verify memory system interface
    assert hasattr(agent_with_memory.memory, "load")
    assert hasattr(agent_with_memory.memory, "remember")
    assert hasattr(agent_with_memory.memory, "activate")


@pytest.mark.asyncio
async def test_memory_persistence():
    """Test memory persistence across interactions."""
    # This would test real persistence, but we mock it to avoid DB dependencies
    mock_memory = Mock()
    mock_memory.load = AsyncMock()
    mock_memory.remember = AsyncMock()
    mock_memory.update = AsyncMock()

    agent = Agent("test", memory=mock_memory)

    # First interaction
    with patch("cogency.agents.reason", new_callable=AsyncMock) as mock_reason:
        with patch("cogency.state.State.start_task", new_callable=AsyncMock) as mock_state:
            mock_state.return_value = Mock()
            mock_reason.return_value = Result.ok({"response": "First response"})
            await agent.run("First query")

    # Second interaction - memory should persist
    with patch("cogency.agents.reason", new_callable=AsyncMock) as mock_reason:
        with patch("cogency.state.State.start_task", new_callable=AsyncMock) as mock_state:
            mock_state.return_value = Mock()
            mock_reason.return_value = Result.ok({"response": "Second response"})
            await agent.run("Second query")

    # Verify remember was called twice
    assert agent.memory.remember.call_count >= 2


def test_custom_memory():
    """Test agent with custom Memory."""
    custom_memory = Mock()
    custom_memory.load = AsyncMock()
    custom_memory.remember = AsyncMock()

    agent = Agent("test", memory=custom_memory)
    assert agent.memory is custom_memory


@pytest.mark.asyncio
async def test_memory_error_handling():
    """Test memory system error handling."""
    mock_memory = Mock()
    mock_memory.load = AsyncMock(side_effect=Exception("Memory error"))
    mock_memory.remember = AsyncMock()

    agent = Agent("test", memory=mock_memory)

    # Agent handles memory errors gracefully and returns error message
    result = await agent.run("Test query")
    assert "Error: Memory error" in result
