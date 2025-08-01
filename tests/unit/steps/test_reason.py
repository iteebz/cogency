"""Test reason step - focused reasoning and decision making."""

from unittest.mock import AsyncMock

import pytest

from cogency.state import State
from cogency.steps.reason import reason
from tests.conftest import MockLLM


@pytest.fixture
def state():
    """Clean state for testing."""
    return State(query="test query", debug=True)


@pytest.mark.asyncio
async def test_reason_basic(state, tools, mock_llm):
    """Test basic reasoning functionality."""
    notifier = AsyncMock()

    result = await reason(state, notifier, mock_llm, tools, memory=None)

    # Should complete without error
    assert notifier.called
    # Result can be None or string depending on Flow implementation
    assert result is None or isinstance(result, str)


@pytest.mark.asyncio
async def test_reason_with_memory(state, tools, mock_llm):
    """Test reasoning with memory context."""
    from unittest.mock import Mock

    notifier = AsyncMock()
    mock_memory = Mock()
    mock_memory.recall = AsyncMock(return_value="memory context")

    result = await reason(state, notifier, mock_llm, tools, memory=mock_memory)

    # Should complete and use memory
    assert notifier.called
    assert result is None or isinstance(result, str)


@pytest.mark.asyncio
async def test_reason_with_identity(state, tools, mock_llm):
    """Test reasoning with identity context."""
    notifier = AsyncMock()

    result = await reason(state, notifier, mock_llm, tools, memory=None, identity="test assistant")

    # Should complete with identity
    assert notifier.called
    assert result is None or isinstance(result, str)


@pytest.mark.asyncio
async def test_reason_llm_failure(state, tools, mock_llm):
    """Test handling of LLM failures."""
    llm = MockLLM(should_fail=True)
    notifier = AsyncMock()

    # Should raise exception when LLM fails since no robust handling is in place
    with pytest.raises(Exception, match="Mock LLM failure"):
        await reason(state, notifier, llm, tools, memory=None)
