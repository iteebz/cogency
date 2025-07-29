"""Detection utility tests."""

from unittest.mock import patch

import pytest

from cogency.utils.detection import detect_provider


def test_first_available():
    providers = {"openai": "OPENAI", "anthropic": "ANTHROPIC"}
    
    with patch("cogency.utils.keys.KeyManager._detect_keys_from_env") as mock_detect:
        mock_detect.side_effect = [{"api_key": "test"}, None]
        
        result = detect_provider(providers)
        assert result == "openai"


def test_second_available():
    providers = {"openai": "OPENAI", "anthropic": "ANTHROPIC"}
    
    with patch("cogency.utils.keys.KeyManager._detect_keys_from_env") as mock_detect:
        mock_detect.side_effect = [None, {"api_key": "test"}]
        
        result = detect_provider(providers)
        assert result == "anthropic"


def test_fallback():
    providers = {"openai": "OPENAI", "anthropic": "ANTHROPIC"}
    
    with patch("cogency.utils.keys.KeyManager._detect_keys_from_env") as mock_detect:
        mock_detect.return_value = None
        
        result = detect_provider(providers, fallback="openai")
        assert result == "openai"


def test_no_keys_no_fallback():
    providers = {"openai": "OPENAI", "anthropic": "ANTHROPIC"}
    
    with patch("cogency.utils.keys.KeyManager._detect_keys_from_env") as mock_detect:
        mock_detect.return_value = None
        
        with pytest.raises(ValueError) as exc_info:
            detect_provider(providers)
        
        assert "No API keys found" in str(exc_info.value)
        assert "OPENAI_API_KEY" in str(exc_info.value)
        assert "ANTHROPIC_API_KEY" in str(exc_info.value)


def test_exception_handling():
    providers = {"openai": "OPENAI", "anthropic": "ANTHROPIC"}
    
    with patch("cogency.utils.keys.KeyManager._detect_keys_from_env") as mock_detect:
        mock_detect.side_effect = [Exception("test error"), {"api_key": "test"}]
        
        result = detect_provider(providers)
        assert result == "anthropic"