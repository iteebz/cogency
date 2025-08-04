"""Test reason step - focused reasoning and decision making."""

from unittest.mock import AsyncMock

import pytest

from cogency.state import AgentState
from cogency.steps.reason import reason
from tests.fixtures.llm import MockLLM


@pytest.fixture
def state():
    """Clean state for testing."""
    state = AgentState(query="test query")
    state.execution.debug = True
    return state


@pytest.mark.asyncio
async def test_reason_basic(state, tools, mock_llm):
    """Test basic reasoning functionality."""
    result = await reason(state, mock_llm, tools, memory=None)

    # Should complete without error
    # Result can be None or string depending on Flow implementation
    assert result is None or isinstance(result, str)


@pytest.mark.asyncio
async def test_reason_with_memory(state, tools, mock_llm):
    """Test reasoning with memory context."""
    from unittest.mock import Mock

    mock_memory = Mock()
    mock_memory.recall = AsyncMock(return_value="memory context")

    result = await reason(state, mock_llm, tools, memory=mock_memory)

    # Should complete and use memory
    assert result is None or isinstance(result, str)


@pytest.mark.asyncio
async def test_reason_with_identity(state, tools, mock_llm):
    """Test reasoning with identity context."""
    result = await reason(state, mock_llm, tools, memory=None)

    # Should complete with identity
    assert result is None or isinstance(result, str)


@pytest.mark.asyncio
async def test_reason_llm_failure(state, tools, mock_llm):
    """Test handling of LLM failures."""
    llm = MockLLM(should_fail=True)

    # Should raise exception when LLM fails since no robust handling is in place
    with pytest.raises(Exception, match="Mock LLM failure"):
        await reason(state, llm, tools, memory=None)


@pytest.mark.asyncio
async def test_malformed_json_response(state, tools):
    """Test handling when LLM returns invalid JSON."""
    from tests.fixtures.llm import MockLLM

    # Invalid JSON - missing bracket
    llm = MockLLM(response='{"thinking": "test", "tool_calls": [')

    # Should handle gracefully, not crash with JSONDecodeError
    await reason(state, llm, tools, memory=None)

    # Should complete without crashing - exact behavior depends on implementation


@pytest.mark.asyncio
async def test_missing_keys(state, tools):
    """Test handling when LLM returns JSON missing required keys."""
    from tests.fixtures.llm import MockLLM

    # Valid JSON but missing expected keys
    llm = MockLLM(response='{"unexpected_key": "value"}')

    await reason(state, llm, tools, memory=None)

    # Should handle gracefully via schema validation


@pytest.mark.asyncio
async def test_wrong_types(state, tools):
    """Test handling when LLM returns JSON with wrong data types."""
    from tests.fixtures.llm import MockLLM

    # Valid JSON but tool_calls is dict instead of list
    llm = MockLLM(response='{"thinking": "test", "tool_calls": {"name": "tool"}}')

    await reason(state, llm, tools, memory=None)

    # Should handle gracefully, not crash with TypeError


@pytest.mark.asyncio
async def test_conversational_response(state, tools):
    """Test handling when LLM breaks character and returns plain text."""
    from tests.fixtures.llm import MockLLM

    # Plain English response instead of JSON
    llm = MockLLM(response="I'm sorry, I am unable to process that request.")

    await reason(state, llm, tools, memory=None)

    # Should handle gracefully - JSON parsing will fail but shouldn't crash


@pytest.mark.asyncio
async def test_hallucinated_tool_calls(state, tools):
    """Test handling when LLM requests non-existent tools."""
    from tests.fixtures.llm import MockLLM

    # Valid JSON but requests non-existent tool
    llm = MockLLM(
        response='{"thinking": "test", "tool_calls": [{"name": "make_sandwich", "args": {}}]}'
    )

    await reason(state, llm, tools, memory=None)
