"""Test Cogency-specific decorator integration."""

from unittest.mock import patch

import pytest

from cogency.resilience import safe


@pytest.mark.asyncio
async def test_safe_agent():
    from cogency import Agent
    from tests.conftest import MockLLM

    async def mock_stream(self, query, user_id="default"):
        yield "2"

    with patch("cogency.agent.detect_llm", return_value=MockLLM()):
        with patch.object(Agent, "stream", mock_stream):
            agent = Agent("test", memory=False)

            result = await agent.run("What is 1+1?")
            assert result is not None
