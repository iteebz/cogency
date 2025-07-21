"""Test Respond node - essential tests only."""
import pytest
from unittest.mock import AsyncMock

from cogency.nodes.respond import respond, build_prompt
from cogency.state import State
from cogency.context import Context
from cogency.output import Output
from cogency.llm.base import BaseLLM


class MockLLM(BaseLLM):
    def __init__(self, response: str = "Test response", should_fail: bool = False):
        self.provider_name = "mock"
        self.response = response
        self.should_fail = should_fail
        self.stream_chunks = response.split(" ") if response else []
    
    async def run(self, messages, **kwargs):
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
    # Basic
    result = build_prompt()
    assert "conversational" in result
    
    # With tool results
    result = build_prompt(has_tool_results=True)
    assert "tool results" in result
    
    # With system prompt
    result = build_prompt(system_prompt="You are helpful.")
    assert "You are helpful." in result


@pytest.mark.asyncio
async def test_respond_basic(state):
    """Test basic respond functionality."""
    llm = MockLLM("Hello world")
    state.output = AsyncMock()
    
    result = await respond(state, llm=llm)
    
    assert result["final_response"] == "Hello world "
    assert result["next_node"] == "END"
    assert len(state.context.messages) >= 2


@pytest.mark.asyncio
async def test_respond_with_tool_results(state):
    """Test respond with tool execution results."""
    llm = MockLLM("Weather is sunny")
    state.output = AsyncMock()
    state["execution_results"] = {"success": True, "results": [{"temperature": "72F"}]}
    
    result = await respond(state, llm=llm)
    
    assert result["final_response"] == "Weather is sunny "
    assert result["next_node"] == "END"


@pytest.mark.asyncio
async def test_respond_error_handling(state):
    """Test respond handles LLM failures."""
    llm = MockLLM(should_fail=True)
    state.output = AsyncMock()
    
    result = await respond(state, llm=llm)
    
    assert "technical issue" in result["final_response"]
    assert result["next_node"] == "END"


@pytest.mark.asyncio
async def test_respond_with_stopping_reason(state):
    """Test respond with stopping reason fallback."""
    llm = MockLLM("Fallback response")
    state.output = AsyncMock()
    state["stopping_reason"] = "max_iterations_reached"
    
    result = await respond(state, llm=llm)
    
    assert result["final_response"] == "Fallback response "
    assert result["next_node"] == "END"