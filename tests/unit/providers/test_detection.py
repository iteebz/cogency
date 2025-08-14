"""Tests for provider detection and auto-configuration."""

from unittest.mock import Mock, patch

import pytest

from cogency.providers.base import Provider
from cogency.providers.utils.detection import (
    _detect_embed_provider,
    _detect_llm_provider,
    _detect_provider,
    detect_embed,
    detect_llm,
)


@patch("cogency.providers.utils.detection.Credentials.detect")
def test_detect_llm_provider_gemini_first(mock_detect):
    """Test LLM detection prefers Gemini when available."""
    # Mock Gemini available
    mock_detect.side_effect = lambda provider: {"api_key": "test"} if provider == "gemini" else None

    with patch("cogency.providers.utils.detection.Gemini") as mock_gemini_class:
        mock_gemini_instance = Mock()
        mock_gemini_class.return_value = mock_gemini_instance

        result = _detect_llm_provider()

        assert result is mock_gemini_instance
        mock_gemini_class.assert_called_once()


@patch("cogency.providers.utils.detection.Credentials.detect")
def test_detect_llm_provider_openai_fallback(mock_detect):
    """Test LLM detection falls back to OpenAI."""
    # Mock no Gemini, but OpenAI available
    mock_detect.side_effect = lambda provider: {"api_key": "test"} if provider == "openai" else None

    with patch("cogency.providers.utils.detection.OpenAI") as mock_openai_class:
        mock_openai_instance = Mock()
        mock_openai_class.return_value = mock_openai_instance

        result = _detect_llm_provider()

        assert result is mock_openai_instance
        mock_openai_class.assert_called_once()


@patch("cogency.providers.utils.detection.Credentials.detect")
def test_detect_llm_provider_default_openai(mock_detect):
    """Test LLM detection raises error when no credentials found."""
    # Mock no credentials found
    mock_detect.return_value = None

    # Should raise ValueError when no credentials are available
    with pytest.raises(ValueError, match="No LLM API keys found"):
        _detect_llm_provider()


@patch("cogency.providers.utils.detection.Credentials.detect")
def test_detect_embed_provider_nomic_first(mock_detect):
    """Test embedding detection prefers Nomic when available."""
    # Mock Nomic available
    mock_detect.side_effect = lambda provider: {"api_key": "test"} if provider == "nomic" else None

    with patch("cogency.providers.utils.detection.Nomic") as mock_nomic_class:
        mock_nomic_instance = Mock()
        mock_nomic_class.return_value = mock_nomic_instance

        result = _detect_embed_provider()

        assert result is mock_nomic_instance
        mock_nomic_class.assert_called_once()


@patch("cogency.providers.utils.detection.Credentials.detect")
def test_detect_embed_provider_nomic_import_error(mock_detect):
    """Test embedding detection handles Nomic import errors."""
    # Mock Nomic available but import fails
    mock_detect.side_effect = lambda provider: {"api_key": "test"} if provider == "openai" else None

    with patch(
        "cogency.providers.utils.detection.Nomic", side_effect=ImportError("Module not found")
    ):
        with patch("cogency.providers.utils.detection.OpenAI") as mock_openai_class:
            mock_openai_instance = Mock()
            mock_openai_class.return_value = mock_openai_instance

            result = _detect_embed_provider()

            assert result is mock_openai_instance


@patch("cogency.providers.utils.detection.Credentials.detect")
def test_detect_embed_provider_openai_fallback(mock_detect):
    """Test embedding detection falls back to OpenAI."""
    # Mock no Nomic, but OpenAI available
    mock_detect.side_effect = lambda provider: {"api_key": "test"} if provider == "openai" else None

    with patch("cogency.providers.utils.detection.Nomic", side_effect=ImportError()):
        with patch("cogency.providers.utils.detection.OpenAI") as mock_openai_class:
            mock_openai_instance = Mock()
            mock_openai_class.return_value = mock_openai_instance

            result = _detect_embed_provider()

            assert result is mock_openai_instance


def test_detect_llm_with_provider():
    """Test detect_llm with explicit provider."""
    mock_provider = Mock(spec=Provider)

    result = detect_llm(mock_provider)
    assert result is mock_provider


def test_detect_llm_invalid_provider():
    """Test detect_llm rejects invalid provider types."""
    with pytest.raises(ValueError, match="Expected Provider instance"):
        detect_llm("invalid_provider")


@patch("cogency.providers.utils.detection._detect_llm_provider")
def test_detect_llm_auto_detection(mock_detect_llm):
    """Test detect_llm auto-detection path."""
    mock_provider = Mock(spec=Provider)
    mock_detect_llm.return_value = mock_provider

    with patch("cogency.events.emit"):
        result = detect_llm()

        assert result is mock_provider
        mock_detect_llm.assert_called_once()


def test_detect_embed_with_provider():
    """Test detect_embed with explicit provider."""
    mock_provider = Mock(spec=Provider)

    result = detect_embed(mock_provider)
    assert result is mock_provider


def test_detect_embed_invalid_provider():
    """Test detect_embed rejects invalid provider types."""
    with pytest.raises(ValueError, match="Expected Provider instance"):
        detect_embed("invalid_provider")


@patch("cogency.providers.utils.detection._detect_embed_provider")
def test_detect_embed_auto_detection(mock_detect_embed):
    """Test detect_embed auto-detection path."""
    mock_provider = Mock(spec=Provider)
    mock_detect_embed.return_value = mock_provider

    with patch("cogency.events.emit"):
        result = detect_embed()

        assert result is mock_provider
        mock_detect_embed.assert_called_once()


@patch("cogency.providers.utils.detection.Credentials.detect")
def test_detect_provider_first_available(mock_detect):
    """Test _detect_provider returns first available provider."""
    providers = {"openai": "OPENAI", "anthropic": "ANTHROPIC", "gemini": "GEMINI"}

    # Mock anthropic available (second in dict)
    mock_detect.side_effect = (
        lambda provider: {"api_key": "test"} if provider == "anthropic" else None
    )

    result = _detect_provider(providers)

    assert result == "anthropic"


@patch("cogency.providers.utils.detection.Credentials.detect")
def test_detect_provider_with_fallback(mock_detect):
    """Test _detect_provider uses fallback when no keys found."""
    providers = {"openai": "OPENAI", "anthropic": "ANTHROPIC"}

    # Mock no keys available
    mock_detect.return_value = None

    result = _detect_provider(providers, fallback="openai")

    assert result == "openai"


@patch("cogency.providers.utils.detection.Credentials.detect")
def test_detect_provider_no_keys_no_fallback(mock_detect):
    """Test _detect_provider raises error when no keys and no fallback."""
    providers = {"openai": "OPENAI", "anthropic": "ANTHROPIC"}

    # Mock no keys available
    mock_detect.return_value = None

    with pytest.raises(ValueError, match="No API keys found"):
        _detect_provider(providers)


@patch("cogency.providers.utils.detection.Credentials.detect")
def test_detect_provider_handles_exceptions(mock_detect):
    """Test _detect_provider handles credential detection exceptions."""
    providers = {"openai": "OPENAI", "anthropic": "ANTHROPIC"}

    # Mock first provider throws exception, second has keys
    def mock_detect_side_effect(provider):
        if provider == "openai":
            raise Exception("Credential error")
        if provider == "anthropic":
            return {"api_key": "test"}
        return None

    mock_detect.side_effect = mock_detect_side_effect

    result = _detect_provider(providers)

    assert result == "anthropic"


@patch("cogency.providers.utils.detection.Credentials.detect")
def test_detect_provider_empty_api_key(mock_detect):
    """Test _detect_provider skips providers with empty api_key."""
    providers = {"openai": "OPENAI", "anthropic": "ANTHROPIC"}

    # Mock first provider has empty key, second has valid key
    def mock_detect_side_effect(provider):
        if provider == "openai":
            return {"api_key": ""}  # Empty key
        if provider == "anthropic":
            return {"api_key": "valid_key"}
        return None

    mock_detect.side_effect = mock_detect_side_effect

    result = _detect_provider(providers)

    assert result == "anthropic"


def test_detect_provider_error_message_format():
    """Test _detect_provider error message includes helpful information."""
    providers = {"openai": "OPENAI", "anthropic": "ANTHROPIC"}

    with patch("cogency.providers.utils.detection.Credentials.detect", return_value=None):
        with pytest.raises(ValueError) as exc_info:
            _detect_provider(providers)

        error_msg = str(exc_info.value)
        assert "Available providers: openai, anthropic" in error_msg
        assert "OPENAI_API_KEY" in error_msg
        assert "ANTHROPIC_API_KEY" in error_msg
        assert "github.com/iteebz/cogency#installation" in error_msg
