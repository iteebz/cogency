from unittest.mock import patch

from cogency import Agent
from cogency.lib.llms import Gemini, OpenAI


def test_llm_provider_behavior():
    """LLM provider creation, switching, and capability validation."""

    # Provider factory creates proper instances with API keys
    with patch("cogency.lib.credentials.detect_api_key") as mock_detect_key:
        mock_detect_key.return_value = "test-key"

        openai_agent = Agent(llm="openai")
        gemini_agent = Agent(llm="gemini")

        # Correct provider types created
        assert isinstance(openai_agent.config.llm, OpenAI)
        assert isinstance(gemini_agent.config.llm, Gemini)

        # API keys passed through (verify factory uses provided keys)
        assert openai_agent.config.llm.api_key == "test-key"
        assert gemini_agent.config.llm.api_key == "test-key"

        # Required capabilities present
        assert hasattr(openai_agent.config.llm, "generate")
        assert hasattr(gemini_agent.config.llm, "generate")
        assert openai_agent.config.llm.resumable is True
        assert gemini_agent.config.llm.resumable is True

    # Invalid providers fail gracefully
    try:
        Agent(llm="nonexistent_provider")
        raise AssertionError("Should raise exception")
    except (ValueError, ImportError, KeyError):
        pass
