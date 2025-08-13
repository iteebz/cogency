"""Error boundary integration: System resilience and recovery."""

import pytest

from cogency import Agent
from cogency.tools import Files


@pytest.mark.integration
@pytest.mark.asyncio
async def test_error_boundaries():
    """System handles errors gracefully without crashing."""
    agent = Agent("test", tools=[Files()])

    # Request that should cause tool error
    result, conv_id = await agent.run("Read file at /completely/invalid/path/file.txt")

    # Should return error message, not crash
    assert isinstance(result, str)
    assert len(result) > 0
    assert isinstance(conv_id, str)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_memory_error_recovery():
    """Memory errors don't crash the system."""
    agent = Agent("test", memory=True)

    # Extreme case - very long input
    large_input = "Remember this: " + "x" * 10000
    result, conv_id = await agent.run(large_input, user_id="test")

    # Should handle gracefully
    assert isinstance(result, str)
    assert len(result) > 0
    assert isinstance(conv_id, str)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_invalid_input_handling():
    """System handles invalid inputs gracefully."""
    agent = Agent("test")

    # Test edge cases
    result1, conv_id1 = await agent.run("", user_id="test")  # Empty query
    result2, conv_id2 = await agent.run("\n\t  \n", user_id="test")  # Whitespace only

    # Should handle without crashing
    assert isinstance(result1, str)
    assert isinstance(result2, str)
    assert isinstance(conv_id1, str)
    assert isinstance(conv_id2, str)
