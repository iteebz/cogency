"""Test Respond node - essential tests only."""

import pytest
from resilient_result import Result
from resilient_result import Result as ResilientResult

from cogency.context import Context
from cogency.phases.respond import prompt_response, respond
from cogency.state import State
from tests.conftest import MockLLM, create_mock_llm


@pytest.fixture
def context():
    ctx = Context("test query")
    ctx.add_message("user", "What is the weather?")
    return ctx


@pytest.fixture
def state(context):
    return State(context=context, query="test query")


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

    result = await respond(state, llm=llm, tools=[])

    assert result.success
    updated_state = result.data
    assert updated_state["final_response"] == "Hello world"
    assert updated_state["next_node"] == "END"
    assert len(state.context.chat) >= 2


@pytest.mark.asyncio
async def test_with_tools(state):
    llm = create_mock_llm("Weather is sunny")
    state["execution_results"] = Result.ok([{"temperature": "72F"}])

    result = await respond(state, llm=llm, tools=[])

    assert result.success
    updated_state = result.data
    assert updated_state["final_response"] == "Weather is sunny"
    assert updated_state["next_node"] == "END"


@pytest.mark.asyncio
async def test_error_handling(state):
    from cogency.services.llm.cache import get_cache

    # Clear cache to avoid interference from other tests
    cache = get_cache()
    await cache.clear()

    llm = MockLLM(should_fail=True)

    result = await respond(state, llm=llm, tools=[])

    assert result.success
    updated_state = result.data
    assert "issue" in updated_state["final_response"].lower()
    assert updated_state["next_node"] == "END"


@pytest.mark.asyncio
async def test_stop_reason(state):
    llm = create_mock_llm("Fallback response")
    state["stop_reason"] = "max_iterations_reached"

    result = await respond(state, llm=llm, tools=[])

    assert result.success
    updated_state = result.data
    assert updated_state["final_response"] == "Fallback response"
    assert updated_state["next_node"] == "END"
