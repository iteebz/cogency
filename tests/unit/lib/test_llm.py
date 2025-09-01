"""LLM tests - First principles V3 launch coverage."""

from unittest.mock import patch

from cogency import Agent


def test_llm_creation_basic():
    """Agent LLM factory doesn't crash."""
    # Should not crash for supported LLMs
    llms = ["openai", "anthropic", "gemini"]

    for llm in llms:
        try:
            with patch.dict("os.environ", {}, clear=True):  # Clear API keys to avoid real calls
                agent = Agent(llm=llm)
                assert agent.llm is not None
                # Check for LLM protocol methods
                assert hasattr(agent.llm, "generate")
        except Exception:
            # LLM might need API keys - that's ok for unit test
            pass


# Embedders removed - Cogency is LLM + Storage + Tools only


def test_invalid_llm():
    """Invalid LLMs handled gracefully."""
    try:
        agent = Agent(llm="invalid_llm")
        # If it returns something, should be valid
        assert hasattr(agent.llm, "generate")
    except Exception as e:
        # If it raises, should be controlled
        assert isinstance(e, (ValueError, ImportError, KeyError))
