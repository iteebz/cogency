"""Test Respond node - essential tests only."""

from unittest.mock import AsyncMock, Mock

import pytest
from resilient_result import Result

from cogency.providers import LLMCache
from cogency.state import AgentState
from cogency.steps.respond import respond
from cogency.steps.respond.prompts import prompt_response
from tests.fixtures.llm import MockLLM, mock_llm


@pytest.fixture
def state():
    return AgentState(query="test query")


def test_prompt():
    # Basic knowledge-only prompt
    result = prompt_response("test query")
    assert "USER QUERY" in result
    assert "test query" in result

    # With tool results
    result = prompt_response("test query", has_tool_results=True, tool_summary="search results")
    assert "TOOL RESULTS" in result
    assert "search results" in result


@pytest.mark.asyncio
async def test_basic(state, mock_llm):
    mock_llm.response = "Hello world"

    await respond(state, AsyncMock(), llm=mock_llm, tools=[])

    assert state.execution.response is not None
    assert state.execution.stop_reason is None  # The respond function doesn't set this
    assert len(state.execution.messages) >= 1


@pytest.mark.asyncio
async def test_tools(state, mock_llm):
    mock_llm.response = "Weather is sunny"
    state.result = Result.ok([{"temperature": "72F"}])

    await respond(state, AsyncMock(), llm=mock_llm, tools=[])

    assert state.execution.response is not None
    assert state.execution.stop_reason is None


@pytest.mark.asyncio
async def test_error(state):
    # Clear cache to avoid interference from other tests
    cache = LLMCache()
    await cache.clear()

    llm = MockLLM(should_fail=True)

    await respond(state, AsyncMock(), llm=llm, tools=[])

    assert state.execution.response == "I'm here to help. How can I assist you?"
    assert state.execution.stop_reason is None


@pytest.mark.asyncio
async def test_stop(state, mock_llm):
    mock_llm.response = "Fallback response"
    state.execution.stop_reason = "depth_reached"

    await respond(state, AsyncMock(), llm=mock_llm, tools=[])

    assert state.execution.response is not None
    assert state.execution.stop_reason == "depth_reached"


@pytest.mark.asyncio
async def test_no_q(state, mock_llm):
    mock_llm.response = "Hello"
    state.execution.query = ""

    await respond(state, AsyncMock(), llm=mock_llm, tools=[])

    assert state.execution.response is not None
    assert state.execution.stop_reason is None


@pytest.mark.asyncio
async def test_no_ctx(state, mock_llm):
    mock_llm.response = "Hello"
    state.execution.messages = []

    await respond(state, AsyncMock(), llm=mock_llm, tools=[])

    assert state.execution.response is not None
    assert state.execution.stop_reason is None


@pytest.mark.asyncio
async def test_no_llm(state):
    # The @robust decorator handles None llm gracefully, so no exception is raised
    await respond(state, AsyncMock(), llm=None, tools=[])
    # Should have some default response or handle gracefully
    assert state.execution.response is not None or state.execution.stop_reason is not None


@pytest.mark.asyncio
async def test_no_tools(state, mock_llm):
    mock_llm.response = "Hello"

    await respond(state, AsyncMock(), llm=mock_llm, tools=[])

    assert state.execution.response is not None
    assert state.execution.stop_reason is None


@pytest.mark.asyncio
async def test_empty_tools(state, mock_llm):
    mock_llm.response = "Hello"

    await respond(state, AsyncMock(), llm=mock_llm, tools=[])

    assert state.execution.response is not None
    assert state.execution.stop_reason is None


@pytest.mark.asyncio
async def test_already_set(state, mock_llm):
    mock_llm.response = "This should not be used"
    state.execution.response = "This is the final answer"

    await respond(state, AsyncMock(), llm=mock_llm, tools=[])

    assert state.execution.response == "This is the final answer"
    assert state.execution.stop_reason is None


@pytest.mark.asyncio
async def test_resilient(state, mock_llm):
    mock_llm.response = "Hello"

    await respond(state, AsyncMock(), llm=mock_llm, tools=[])

    assert state.execution.response is not None
