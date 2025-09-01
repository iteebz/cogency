"""LLM integration tests - switching mechanics."""

from unittest.mock import patch

import pytest

from cogency import Agent
from cogency.lib.llms import Gemini, OpenAI


@pytest.mark.asyncio
async def test_openai_provider_creation():
    """OpenAI provider creates correctly."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        agent = Agent(llm="openai")
        assert isinstance(agent.llm, OpenAI)
        assert agent.llm.api_key == "test-key"


@pytest.mark.asyncio
async def test_gemini_provider_creation():
    """Gemini provider creates correctly."""
    with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
        agent = Agent(llm="gemini")
        assert isinstance(agent.llm, Gemini)
        assert agent.llm.api_key == "test-key"


@pytest.mark.asyncio
async def test_provider_switching():
    """Can switch providers between agent instances."""
    mock_response = "Test response"

    with patch("cogency.core.agent.consciousness_stream") as mock_stream:
        # Mock async generator
        async def mock_events():
            yield {"type": "respond", "content": mock_response}

        mock_stream.side_effect = lambda *args, **kwargs: mock_events()

        # Test OpenAI agent
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            openai_agent = Agent(llm="openai")
            response1 = await openai_agent("Hello")

        # Test Gemini agent
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            gemini_agent = Agent(llm="gemini")
            response2 = await gemini_agent("Hello")

        # Both should work
        assert response1 == mock_response
        assert response2 == mock_response
        assert mock_stream.call_count == 2


@pytest.mark.asyncio
async def test_llm_capabilities():
    """LLMs expose correct capabilities."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test", "GEMINI_API_KEY": "test"}):
        openai = OpenAI()
        gemini = Gemini()

        # Both should have WebSocket capability
        assert hasattr(openai, "resumable")
        assert hasattr(gemini, "resumable")
        assert openai.resumable is True
        assert gemini.resumable is True
