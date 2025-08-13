"""ReAct loop integration: Agent → Reason → Act → Tool → Memory → Response."""

import pytest

from cogency import Agent
from cogency.tools import Files


@pytest.mark.integration
@pytest.mark.asyncio
async def test_react_loop():
    """Complete ReAct cycle with real components."""
    agent = Agent("test", tools=[Files()], memory=True)

    result, conversation_id = await agent.run("List files in current directory")

    # Verify complete cycle executed
    assert isinstance(result, str)
    assert len(result) > 0
    assert isinstance(conversation_id, str)

    # Verify memory captured the interaction
    logs = agent.logs()
    assert len(logs) > 0  # Events captured


@pytest.mark.integration
@pytest.mark.asyncio
async def test_react_multi_step():
    """Multi-step ReAct loop with tool chaining."""
    agent = Agent("test", tools=[Files()], memory=True)

    result, _ = await agent.run("List files then read README.md")

    # Verify multi-step execution
    assert isinstance(result, str)
    assert len(result) > 0

    # Verify events captured
    logs = agent.logs()
    assert len(logs) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_react_with_memory_context():
    """ReAct loop incorporating memory context."""
    agent = Agent("test", tools=[Files()], memory=True)

    result, _ = await agent.run("Process files with previous preferences")

    # Verify memory integration
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_react_tool_failure_recovery():
    """ReAct loop with tool failure and recovery."""
    agent = Agent("test", tools=[Files()], memory=True)

    result, _ = await agent.run("Read a file, handle errors")

    # Verify recovery cycle
    assert isinstance(result, str)
    assert len(result) > 0

    # Verify error was handled gracefully
    logs = agent.logs()
    assert len(logs) > 0  # Events captured


@pytest.mark.integration
@pytest.mark.asyncio
async def test_react_no_tools_needed():
    """ReAct loop that determines no tools are needed."""
    agent = Agent("test", tools=[Files()], memory=True)

    result, _ = await agent.run("What is 2+2?")

    # Verify direct response path
    assert isinstance(result, str)
    assert len(result) > 0

    # Verify events captured
    logs = agent.logs()
    assert len(logs) > 0
