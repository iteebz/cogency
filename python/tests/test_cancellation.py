import asyncio

import pytest

from cogency.agent import Agent
from cogency.llm.base import BaseLLM
from cogency.tools.base import BaseTool


class SlowMockLLM(BaseLLM):
    """Mock LLM that takes a long time to respond."""

    def __init__(self, delay: float = 2.0):
        super().__init__(api_key="test")
        self.delay = delay

    async def invoke(self, messages, **kwargs):
        await asyncio.sleep(self.delay)
        return "Mock response after delay"


class SlowMockTool(BaseTool):
    """Mock tool that takes a long time to execute."""

    def __init__(self, delay: float = 2.0):
        super().__init__("slow_tool", "A tool that takes time")
        self.delay = delay

    async def run(self, **kwargs):
        await asyncio.sleep(self.delay)
        return {"result": "slow operation complete"}

    def get_schema(self):
        return "slow_tool()"

    def get_usage_examples(self):
        return ["slow_tool()"]


@pytest.mark.asyncio
async def test_agent_cancellation():
    """Test that agent execution can be cleanly cancelled."""
    llm = SlowMockLLM(delay=5.0)  # 5 second delay
    agent = Agent(name="TestAgent", llm=llm)

    # Create a task that should take 5+ seconds
    task = asyncio.create_task(agent.run("Hello"))

    # Wait a short time then cancel
    await asyncio.sleep(0.1)
    task.cancel()

    # Should raise CancelledError
    with pytest.raises(asyncio.CancelledError):
        await task


@pytest.mark.asyncio
async def test_tool_cancellation():
    """Test that tool execution can be cleanly cancelled."""
    from cogency.llm.gemini import GeminiLLM

    # Use real LLM but slow tool
    try:
        llm = GeminiLLM(api_keys="test-key")
    except Exception:
        # Skip if no real LLM available, consider more specific exception if known
        pytest.skip("No Gemini API key available")

    slow_tool = SlowMockTool(delay=5.0)
    agent = Agent(name="TestAgent", llm=llm, tools=[slow_tool])

    # Create task that will trigger tool usage
    task = asyncio.create_task(agent.run("Use the slow tool"))

    # Cancel after short delay
    await asyncio.sleep(0.1)
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task


@pytest.mark.asyncio
async def test_cancellation_propagation():
    """Test that cancellation properly propagates through the execution stack."""
    llm = SlowMockLLM(delay=10.0)
    agent = Agent(name="TestAgent", llm=llm)

    # Start agent task
    agent_task = asyncio.create_task(agent.run("Test message"))

    # Cancel after 0.5 seconds
    await asyncio.sleep(0.5)
    agent_task.cancel()

    # Should raise CancelledError
    with pytest.raises(asyncio.CancelledError):
        await agent_task
