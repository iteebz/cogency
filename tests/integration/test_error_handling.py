"""Error handling integration: Graceful failure and recovery."""

import pytest

from cogency import Agent
from cogency.tools import Files


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tool_error_handling():
    """Agent handles tool errors gracefully."""
    agent = Agent("test", tools=[Files()])

    # Request that might cause tool error
    result, conv_id = await agent.run("Read non-existent file: /fake/path/file.txt")

    # Should return error message, not crash
    assert isinstance(result, str)
    assert len(result) > 0
    assert isinstance(conv_id, str)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_invalid_user_handling():
    """System handles invalid user scenarios."""
    agent = Agent("test", memory=True)

    # Test with edge case user IDs
    result1, conv_id1 = await agent.run("Test message", user_id="")
    result2, conv_id2 = await agent.run("Test message", user_id=None)

    # Should handle gracefully
    assert isinstance(result1, str)
    assert isinstance(result2, str)
    assert isinstance(conv_id1, str)
    assert isinstance(conv_id2, str)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_large_input_handling():
    """System handles large inputs without crashing."""
    agent = Agent("test")

    # Very large input
    large_input = "Test message. " * 1000
    result, conv_id = await agent.run(large_input)

    # Should process without crashing
    assert isinstance(result, str)
    assert len(result) > 0
    assert isinstance(conv_id, str)
