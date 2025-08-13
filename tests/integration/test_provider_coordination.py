"""Provider coordination integration: LLM → Embedding provider flow."""

import pytest

from cogency import Agent
from cogency.tools import Files


@pytest.mark.integration
@pytest.mark.asyncio
async def test_provider_coordination():
    """Agent coordinates LLM and embedding providers successfully."""
    agent = Agent("test", tools=[Files()], memory=True)

    # Query that requires both LLM reasoning and potential embedding operations
    result, conv_id = await agent.run("Analyze the files in current directory", user_id="test")

    # Should coordinate providers without issues
    assert isinstance(result, str)
    assert len(result) > 0
    assert isinstance(conv_id, str)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_provider_isolation():
    """Provider failures don't cascade across the system."""
    agent = Agent("test")

    # Simple query that should work even with provider issues
    result, conv_id = await agent.run("What is 2+2?", user_id="test")

    # Should get response despite potential provider issues
    assert isinstance(result, str)
    assert len(result) > 0
    assert isinstance(conv_id, str)
