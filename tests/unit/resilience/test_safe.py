"""Test Cogency-specific decorator integration."""

from unittest.mock import patch

import pytest

from cogency.resilience import safe


class TestIntegration:
    """Integration tests with real agent functionality."""

    @pytest.mark.asyncio
    async def test_safe_agent(self):
        """Test that agents work with @safe protected LLMs."""
        from cogency import Agent
        from tests.conftest import MockLLM

        async def mock_stream(self, query, user_id="default"):
            yield "2"

        # Mock LLM detection and stream method to avoid LLM overhead
        with patch("cogency.agent.detect_llm", return_value=MockLLM()):
            with patch.object(Agent, "stream", mock_stream):
                # Create agent with memory disabled
                agent = Agent("test", memory=False)

                # Should work normally
                result = await agent.run("What is 1+1?")
                assert result is not None
