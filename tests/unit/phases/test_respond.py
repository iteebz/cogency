"""Test Respond node - essential tests only."""

import pytest
from resilient_result import Result

from cogency.phases.respond import prompt_response, respond
from cogency.services.llm.cache import get_cache
from cogency.state import State
from tests.conftest import MockLLM, create_mock_llm


@pytest.fixture
def state():
    return State(query="test query")


def test_prompt():
    # Basic knowledge-only prompt
    result = prompt_response("test query")
    assert "USER QUERY" in result
    assert "test query" in result

    # With tool results
    result = prompt_response("test query", has_tool_results=True, tool_summary="search results")
    assert "TOOL RESULTS" in result
    assert "search results" in result

    # With system prompt
    result = prompt_response("test query", system_prompt="You are helpful.")
    assert "You are helpful." in result


@pytest.mark.asyncio
async def test_basic(state):
    llm = create_mock_llm("Hello world")

    await respond(state, llm=llm, tools=[])

    assert state.response == "Hello world"
    assert state.stop_reason is None # The respond function doesn't set this
    assert len(state.messages) == 1


@pytest.mark.asyncio
async def test_with_tools(state):
    llm = create_mock_llm("Weather is sunny")
    state.result = Result.ok([{"temperature": "72F"}])

    await respond(state, llm=llm, tools=[])

    assert state.response == "Weather is sunny"
    assert state.stop_reason is None


@pytest.mark.asyncio
async def test_error_handling(state):
    # Clear cache to avoid interference from other tests
    cache = get_cache()
    await cache.clear()

    llm = MockLLM(should_fail=True)

    await respond(state, llm=llm, tools=[])

    assert state.response == "I'm here to help. How can I assist you?"
    assert state.stop_reason is None


@pytest.mark.asyncio
async def test_stop_reason(state):
    llm = create_mock_llm("Fallback response")
    state.stop_reason = "max_iterations_reached"

    await respond(state, llm=llm, tools=[])

    assert state.response == "Fallback response"
    assert state.stop_reason == "max_iterations_reached"


@pytest.mark.asyncio
async def test_no_query(state):
    llm = create_mock_llm("Hello")
    state.query = ""

    await respond(state, llm=llm, tools=[])

    assert state.response == "Hello"
    assert state.stop_reason is None


@pytest.mark.asyncio
async def test_no_context(state):
    llm = create_mock_llm("Hello")
    state.messages = []

    await respond(state, llm=llm, tools=[])

    assert state.response == "Hello"
    assert state.stop_reason is None


@pytest.mark.asyncio
async def test_no_llm(state):
    # The @robust decorator handles None llm gracefully, so no exception is raised
    await respond(state, llm=None, tools=[])
    # Should have some default response or handle gracefully
    assert state.response is not None or state.stop_reason is not None


@pytest.mark.asyncio
async def test_no_tools(state):
    llm = create_mock_llm("Hello")

    await respond(state, llm=llm, tools=[])

    assert state.response == "Hello"
    assert state.stop_reason is None


@pytest.mark.asyncio
async def test_empty_tools(state):
    llm = create_mock_llm("Hello")

    await respond(state, llm=llm, tools=[])

    assert state.response == "Hello"
    assert state.stop_reason is None


@pytest.mark.asyncio
async def test_final_response_already_set(state):
    llm = create_mock_llm("This should not be used")
    state.response = "This is the final answer"

    await respond(state, llm=llm, tools=[])

    assert state.response == "This is the final answer"
    assert state.stop_reason is None


@pytest.mark.asyncio
async def test_result_is_resilient(state):
    llm = create_mock_llm("Hello")

    await respond(state, llm=llm, tools=[])

    assert state.response == "Hello"