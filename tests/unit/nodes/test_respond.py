"""Test Respond node - essential tests only."""

import pytest

from cogency.context import Context
from cogency.nodes.respond import prompt_response, respond
from cogency.output import Output
from cogency.state import State
from cogency.utils.results import ActionResult
from tests.conftest import MockLLM, create_mock_llm


@pytest.fixture
def context():
    ctx = Context("test query")
    ctx.add_message("user", "What is the weather?")
    return ctx


@pytest.fixture
def state(context):
    return State(context=context, query="test query", output=Output())


def test_build_prompt():
    """Test prompt building."""
    # Basic knowledge-only prompt
    result = prompt_response("test query")
    assert "USER QUERY" in result
    assert "test query" in result

    # With tool results
    result = prompt_response(
        "test query", has_tool_results=True, tool_results_summary="search results"
    )
    assert "TOOL RESULTS" in result
    assert "search results" in result

    # With system prompt
    result = prompt_response("test query", system_prompt="You are helpful.")
    assert "You are helpful." in result


@pytest.mark.asyncio
async def test_respond_basic(state):
    """Test basic respond functionality."""
    llm = create_mock_llm("Hello world")

    updated_state = await respond(state, llm=llm, tools=[])

    assert updated_state["final_response"] == "Hello world"
    assert updated_state["next_node"] == "END"
    assert len(state.context.messages) >= 2


@pytest.mark.asyncio
async def test_respond_with_tool_results(state):
    """Test respond with tool execution results."""
    from unittest.mock import AsyncMock

    llm = create_mock_llm("Weather is sunny")
    state.output = AsyncMock()
    state["execution_results"] = ActionResult.ok([{"temperature": "72F"}])

    updated_state = await respond(state, llm=llm, tools=[])

    assert updated_state["final_response"] == "Weather is sunny"
    assert updated_state["next_node"] == "END"


@pytest.mark.asyncio
async def test_respond_error_handling(state):
    """Test respond handles LLM failures."""
    from unittest.mock import AsyncMock

    from cogency.types.cache import get_cache

    # Clear cache to avoid interference from other tests
    cache = get_cache()
    await cache.clear()

    llm = MockLLM(should_fail=True)
    state.output = AsyncMock()

    updated_state = await respond(state, llm=llm, tools=[])

    assert "issue" in updated_state["final_response"].lower()
    assert updated_state["next_node"] == "END"


@pytest.mark.asyncio
async def test_with_stopping_reason(state):
    """Test respond with stopping reason fallback."""
    from unittest.mock import AsyncMock

    llm = create_mock_llm("Fallback response")
    state.output = AsyncMock()
    state["stopping_reason"] = "max_iterations_reached"

    updated_state = await respond(state, llm=llm, tools=[])

    assert updated_state["final_response"] == "Fallback response"
    assert updated_state["next_node"] == "END"
