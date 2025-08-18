"""Test provider factory functions."""

from unittest.mock import patch

import pytest


def test_create_llm_string_shortcut():
    """Create LLM from string shortcut."""
    from cogency.lib.providers import create_llm
    from cogency.lib.providers.openai import OpenAI

    with patch("cogency.lib.providers.detect_api_key", return_value="sk-test"):
        llm = create_llm("openai")
        assert isinstance(llm, OpenAI)
        assert llm.api_key == "sk-test"


def test_create_llm_returns_instance():
    """Return object if already an instance."""
    from cogency.lib.providers import create_llm
    from cogency.lib.providers.openai import OpenAI

    provider = OpenAI(api_key="test")
    result = create_llm(provider)
    assert result is provider


def test_create_llm_unknown_provider():
    """Raise error for unknown provider."""
    from cogency.lib.providers import create_llm

    with pytest.raises(ValueError, match="Unknown provider: unknown"):
        create_llm("unknown")


def test_create_llm_missing_api_key():
    """Raise error when API key not found."""
    from cogency.lib.providers import create_llm

    with patch("cogency.lib.providers.detect_api_key", return_value=None):
        with pytest.raises(ValueError, match="OpenAI API key not found"):
            create_llm("openai")
