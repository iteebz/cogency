"""Tests for enhanced reasoning node integration."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from resilient_result import Result

from cogency.phases.reason import reason
from cogency.state import State
from tests.conftest import MockLLM


class MockToolCall:
    def __init__(self, name, args):
        self.name = name
        self.args = args


def mock_llm():
    llm = AsyncMock()
    llm.run = AsyncMock(
        return_value=Result.ok('{"reasoning": "test reasoning", "strategy": "test_strategy"}')
    )
    return llm


def mock_tools():
    tool = Mock()
    tool.name = "test_tool"
    tool.schema = "test schema"
    tool.examples = []
    tool.rules = []
    return [tool]


def basic_state():
    return State(query="test query")


@pytest.mark.asyncio
async def test_cognition_initialization():
    state = basic_state()
    await reason(state, llm=mock_llm(), tools=mock_tools())

    assert isinstance(state, State)
    assert hasattr(state, "situation_summary")
    assert isinstance(state.actions, list)
    assert hasattr(state, "attempts")


@pytest.mark.asyncio
async def test_iteration_tracking():
    state = basic_state()
    state.iteration = 2

    result = await reason(state, llm=mock_llm(), tools=mock_tools())

    assert result.success
    assert isinstance(state, State)
    assert state.iteration == 3


@pytest.mark.asyncio
async def test_depth():
    state = basic_state()
    state.iteration = 5
    state.depth = 5

    await reason(state, llm=mock_llm(), tools=mock_tools())

    assert isinstance(state, State)
    assert state.stop_reason == "depth_reached"


@pytest.mark.asyncio
async def test_llm_error():
    state = basic_state()
    llm = mock_llm()
    llm.run.side_effect = Exception("LLM error")

    with patch("asyncio.sleep", new_callable=AsyncMock):
        result = await reason(state, llm=llm, tools=mock_tools())
        assert not result.success
        assert "LLM error" in str(result.error)
