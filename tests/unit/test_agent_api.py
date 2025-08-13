"""Test Agent API surface prevents method creep regression."""

import inspect

import pytest

from cogency import Agent


@pytest.fixture
def agent():
    """Clean agent for API testing."""
    return Agent("test", memory=False)


def test_api_surface():
    """Agent has exactly 5 public methods."""
    public_methods = [
        name
        for name, method in inspect.getmembers(Agent, predicate=inspect.isfunction)
        if not name.startswith("_")
    ]

    expected = {"run", "run_sync", "stream", "get_memory", "logs"}
    actual = set(public_methods)

    assert actual == expected, f"API changed. Expected: {expected}, Got: {actual}"


def test_no_deprecated_methods():
    """Deprecated methods don't exist."""
    agent = Agent("test")

    deprecated = ["execute", "run_async", "_execute_internal"]

    for method_name in deprecated:
        assert not hasattr(agent, method_name), f"Deprecated method {method_name} still exists"


@pytest.mark.asyncio
async def test_run_is_primary():
    """run() is the primary async method."""
    agent = Agent("test", memory=False)

    # Should work without issues
    result = await agent.run("test")
    assert isinstance(result, tuple)


def test_run_sync_wraps_run():
    """run_sync() is sync wrapper."""
    agent = Agent("test", memory=False)

    # Should work without event loop
    result = agent.run_sync("test")
    assert isinstance(result, tuple)
