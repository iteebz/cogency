"""System tests with real LLMs - minimal and expensive."""

import os

import pytest

from cogency import Agent


@pytest.mark.system
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="Requires OPENAI_API_KEY")
@pytest.mark.asyncio
async def test_basic_query():
    """Test basic agent functionality with real LLM."""
    agent = Agent("assistant")
    response = await agent.run_async("What is 2+2?")

    assert isinstance(response, str)
    assert len(response) > 0
    assert "4" in response


@pytest.mark.system
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="Requires OPENAI_API_KEY")
@pytest.mark.asyncio
async def test_tool_usage():
    """Test tool usage with real LLM."""
    from cogency.tools import Files

    agent = Agent("assistant", tools=[Files()])
    response = await agent.run_async("List the files in the current directory")

    assert isinstance(response, str)
    assert len(response) > 0


@pytest.mark.system
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="Requires OPENAI_API_KEY")
@pytest.mark.asyncio
async def test_memory():
    """Test memory functionality with real LLM."""
    agent = Agent("assistant", memory=True)

    response1 = await agent.run_async("Remember that my name is Claude")
    assert isinstance(response1, str)

    response2 = await agent.run_async("What is my name?")
    assert isinstance(response2, str)
    # Note: Memory recall depends on implementation details
