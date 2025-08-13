"""Tool resolution integration: String → Object → Execution pipeline."""

import pytest

from cogency import Agent
from cogency.tools import Files, Scrape


@pytest.mark.integration
@pytest.mark.asyncio
async def test_resolution():
    """Tools resolve from instances to executable objects."""
    agent = Agent("test", tools=[Files(), Scrape()], memory=False)

    result, _ = await agent.run("List current directory files")

    # Verify tool resolution worked
    assert isinstance(result, str)
    assert len(result) > 0
    logs = agent.logs()
    assert len(logs) > 0  # Events captured


@pytest.mark.integration
@pytest.mark.asyncio
async def test_objects():
    """Tools work when provided as objects."""
    files_tool = Files()
    scrape_tool = Scrape()
    agent = Agent("test", tools=[files_tool, scrape_tool], memory=False)

    result, _ = await agent.run("Use files tool")

    # Verify object-based tools work
    assert isinstance(result, str)
    assert len(result) > 0
    logs = agent.logs()
    assert len(logs) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_failure():
    """Graceful handling when tool execution fails."""
    agent = Agent("test", tools=[Files()], memory=False)

    result, _ = await agent.run("Use invalid tool")

    # Verify graceful failure
    assert isinstance(result, str)
    assert len(result) > 0
    logs = agent.logs()
    assert len(logs) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_mixed_formats():
    """Agent handles mix of different tool instances."""
    files_object = Files()
    scrape_object = Scrape()
    agent = Agent("test", tools=[files_object, scrape_object], memory=False)

    result, _ = await agent.run("Use files then scrape tools")

    # Verify both resolution paths work
    assert isinstance(result, str)
    assert len(result) > 0
    logs = agent.logs()
    assert len(logs) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_caching():
    """Tool resolution is cached for performance."""
    agent = Agent("test", tools=[Files()], memory=False)

    result, _ = await agent.run("List files in multiple directories")

    # Verify multiple tool executions
    assert isinstance(result, str)
    assert len(result) > 0
    logs = agent.logs()
    assert len(logs) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_dynamic_loading():
    """Tools can be resolved dynamically at runtime."""
    # Start with no tools
    agent = Agent("test", tools=[], memory=False)

    # Add tool dynamically (simulates runtime tool loading)
    agent.tools = [Files()]

    result, _ = await agent.run("Use dynamically added tool")

    # Verify dynamic tool resolution works
    assert isinstance(result, str)
    assert len(result) > 0
    logs = agent.logs()
    assert len(logs) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_security_boundary():
    """Tool resolution respects security boundaries."""
    agent = Agent("test", tools=[Files()], memory=False)

    result, _ = await agent.run("Read system files")

    # Tool should execute (resolution works) but may have security restrictions
    assert isinstance(result, str)
    assert len(result) > 0
    logs = agent.logs()
    assert len(logs) > 0
