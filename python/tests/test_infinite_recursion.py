"""Tests for infinite recursion prevention and edge cases."""

import pytest
from typing import AsyncIterator

from cogency.agent import Agent
from cogency.context import Context
from cogency.llm.base import BaseLLM
from cogency.types import AgentState, ExecutionTrace


class MockLLM(BaseLLM):
    """Mock LLM for testing with streaming support."""

    def __init__(self, responses=None):
        super().__init__()
        self.responses = responses or []
        self.call_count = 0

    async def invoke(self, messages, **kwargs):
        if self.call_count < len(self.responses):
            response = self.responses[self.call_count]
        else:
            response = "Default response"
        self.call_count += 1
        return response

    async def stream(self, messages, yield_interval=0.0, **kwargs):
        """Mock streaming implementation."""
        response = await self.invoke(messages, **kwargs)
        yield response


@pytest.mark.asyncio
async def test_max_depth_prevents_infinite_loops():
    """Test that max_depth prevents infinite execution loops."""
    # Mock LLM that always wants to continue (would cause infinite loop)
    mock_responses = [
        '{"action": "tool_needed", "reasoning": "Need calculator"}',  # plan
        'TOOL_CALL: calculator(operation="add", x1=1, x2=1)',  # reason
        '{"status": "continue", "assessment": "Keep going"}',  # reflect (tries to continue)
    ] * 20  # Repeat many times to test recursion limit

    mock_llm = MockLLM(mock_responses)
    agent = Agent(name="TestAgent", llm=mock_llm, max_depth=5)

    # This should hit the recursion limit and raise an exception
    from langgraph.errors import GraphRecursionError

    with pytest.raises(GraphRecursionError):
        await agent.run("What is 1 + 1?")


@pytest.mark.asyncio
async def test_agent_handles_basic_workflow():
    """Test agent handles basic workflow without recursion."""
    mock_responses = [
        '{"action": "direct_response", "answer": "Hello world"}',
    ]
    
    mock_llm = MockLLM(mock_responses)
    agent = Agent(name="TestAgent", llm=mock_llm)
    
    result = await agent.run("Hello")
    assert "response" in result
    assert result["response"] == "Hello world"