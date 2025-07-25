"""Test Respond node - essential tests only."""

from unittest.mock import AsyncMock

import pytest

from cogency.context import Context
from cogency.services.llm.base import BaseLLM
from cogency.nodes.respond import prompt_response, respond
from cogency.output import Output
from cogency.state import State
from cogency.utils.results import ActionResult


class MockLLM(BaseLLM):
    def __init__(self, response: str = "Test response", should_fail: bool = False):
        super().__init__(provider_name="mock", api_keys="test-key")
        self.response = response
        self.should_fail = should_fail
        self.stream_chunks = response.split(" ") if response else []

    async def _run_impl(self, messages, **kwargs):
        if self.should_fail:
            raise Exception("LLM API error")
        return self.response

    async def stream(self, messages, **kwargs):
        if self.should_fail:
            raise Exception("LLM streaming error")
        for chunk in self.stream_chunks:
            yield chunk + " "


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
    llm = MockLLM("Hello world")
    state.output = AsyncMock()

    result = await respond(state, llm=llm, tools=[])

    assert result["final_response"] == "Hello world"
    assert result["next_node"] == "END"
    assert len(state.context.messages) >= 2


@pytest.mark.asyncio
async def test_respond_with_tool_results(state):
    """Test respond with tool execution results."""
    llm = MockLLM("Weather is sunny")
    state.output = AsyncMock()
    state["execution_results"] = ActionResult([{"temperature": "72F"}])

    result = await respond(state, llm=llm, tools=[])

    assert result["final_response"] == "Weather is sunny"
    assert result["next_node"] == "END"


@pytest.mark.asyncio
async def test_respond_error_handling(state):
    """Test respond handles LLM failures."""
    from cogency.types.cache import get_cache

    # Clear cache to avoid interference from other tests
    cache = get_cache()
    await cache.clear()

    llm = MockLLM(should_fail=True)
    state.output = AsyncMock()

    result = await respond(state, llm=llm, tools=[])

    assert "Technical issue" in result["final_response"]
    assert result["next_node"] == "END"


@pytest.mark.asyncio
async def test_with_stopping_reason(state):
    """Test respond with stopping reason fallback."""
    llm = MockLLM("Fallback response")
    state.output = AsyncMock()
    state["stopping_reason"] = "max_iterations_reached"

    result = await respond(state, llm=llm, tools=[])

    assert result["final_response"] == "Fallback response"
    assert result["next_node"] == "END"
