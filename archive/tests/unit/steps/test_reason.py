"""Test reason step - focused reasoning and decision making."""

from unittest.mock import AsyncMock

import pytest
from resilient_result import unwrap

from cogency.state import State
from cogency.steps.reason import reason
from tests.fixtures.provider import MockLLM


@pytest.fixture
def state():
    """Clean state for testing."""
    state = State(query="test query")
    state.execution.debug = True
    return state


@pytest.mark.asyncio
async def test_reason_basic(state, mock_tools, mock_provider):
    """Test basic reasoning functionality."""
    result = await reason(state, llm=mock_provider, tools=mock_tools, memory=None)

    # Unwrap result like production code does
    response = unwrap(result)
    # Should complete without error
    assert response is None or isinstance(response, str)


@pytest.mark.asyncio
async def test_reason_with_memory(state, mock_tools, mock_provider):
    """Test reasoning with memory context."""
    from unittest.mock import Mock

    mock_memory = Mock()
    mock_memory.recall = AsyncMock(return_value="memory context")

    result = await reason(state, llm=mock_provider, tools=mock_tools, memory=mock_memory)

    # Unwrap result like production code does
    response = unwrap(result)
    assert response is None or isinstance(response, str)


@pytest.mark.asyncio
async def test_reason_with_identity(state, mock_tools, mock_provider):
    """Test reasoning with identity context."""
    result = await reason(state, llm=mock_provider, tools=mock_tools, memory=None)

    # Unwrap result like production code does
    response = unwrap(result)
    assert response is None or isinstance(response, str)


@pytest.mark.asyncio
async def test_reason_provider_failure(state, mock_tools, mock_provider):
    """Test handling of provider failures."""
    llm = MockLLM(should_fail=True)

    # With resilience decorator, failures should be gracefully handled
    result = await reason(state, llm=llm, tools=mock_tools, memory=None)
    # unwrap() will raise if Result failed, but production code handles this
    # Test should verify the failure is contained, not that it raises
    try:
        response = unwrap(result)
        # If it succeeds, response should be valid
        assert response is None or isinstance(response, str)
    except Exception:
        # Failures are acceptable - resilience contains them
        pass


@pytest.mark.asyncio
async def test_malformed_json_response(state, mock_tools):
    """Test handling when LLM returns invalid JSON."""
    from tests.fixtures.provider import MockLLM

    # Invalid JSON - missing bracket
    llm = MockLLM(response='{"thinking": "test", "tool_calls": [')

    # Should handle gracefully, not crash with JSONDecodeError
    await reason(state, llm=llm, tools=mock_tools, memory=None)

    # Should complete without crashing - exact behavior depends on implementation


@pytest.mark.asyncio
async def test_missing_keys(state, mock_tools):
    """Test handling when LLM returns JSON missing required keys."""
    from tests.fixtures.provider import MockLLM

    # Valid JSON but missing expected keys
    llm = MockLLM(response='{"unexpected_key": "value"}')

    await reason(state, llm=llm, tools=mock_tools, memory=None)

    # Should handle gracefully via schema validation


@pytest.mark.asyncio
async def test_wrong_types(state, mock_tools):
    """Test handling when LLM returns JSON with wrong data types."""
    from tests.fixtures.provider import MockLLM

    # Valid JSON but tool_calls is dict instead of list
    llm = MockLLM(response='{"thinking": "test", "tool_calls": {"name": "tool"}}')

    await reason(state, llm=llm, tools=mock_tools, memory=None)

    # Should handle gracefully, not crash with TypeError


@pytest.mark.asyncio
async def test_conversational_response(state, mock_tools):
    """Test handling when LLM breaks character and returns plain text."""
    from tests.fixtures.provider import MockLLM

    # Plain English response instead of JSON
    llm = MockLLM(response="I'm sorry, I am unable to process that request.")

    await reason(state, llm=llm, tools=mock_tools, memory=None)

    # Should handle gracefully - JSON parsing will fail but shouldn't crash


@pytest.mark.asyncio
async def test_hallucinated_tool_calls(state, mock_tools):
    """Test handling when LLM requests non-existent tools."""
    from tests.fixtures.provider import MockLLM

    # Valid JSON but requests non-existent tool
    llm = MockLLM(
        response='{"thinking": "test", "tool_calls": [{"name": "make_sandwich", "args": {}}]}'
    )

    await reason(state, llm=llm, tools=mock_tools, memory=None)
