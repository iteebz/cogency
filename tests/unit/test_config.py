"""Unit tests for the config module."""
import os
import pytest
from unittest.mock import patch

from cogency.config import get_api_keys


class TestConfig:
    """Tests for the config module."""

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    def test_get_api_keys_single_key(self):
        """Test retrieving a single API key."""
        keys = get_api_keys("openai")
        assert len(keys) == 1
        assert keys[0] == "test-key"

    @patch.dict(os.environ, {
        "ANTHROPIC_API_KEY": "main-key",
        "ANTHROPIC_API_KEY_1": "key1",
        "ANTHROPIC_API_KEY_2": "key2"
    })
    def test_get_api_keys_multiple_keys(self):
        """Test retrieving multiple numbered API keys."""
        keys = get_api_keys("anthropic")
        assert len(keys) == 3
        assert keys[0] == "main-key"
        assert keys[1] == "key1"
        assert keys[2] == "key2"

    @patch.dict(os.environ, {
        "ANTHROPIC_API_KEY_1": "key1",
        "ANTHROPIC_API_KEY_2": "key2"
    })
    def test_get_api_keys_numbered_only(self):
        """Test retrieving only numbered API keys without a base key."""
        keys = get_api_keys("anthropic")
        assert len(keys) == 2
        assert keys[0] == "key1"
        assert keys[1] == "key2"

    @patch.dict(os.environ, {
        "ANTHROPIC_API_KEY": "main-key",
        "ANTHROPIC_API_KEY_1": "key1",
        "ANTHROPIC_API_KEY_3": "key3"  # Note: key2 is missing
    })
    def test_get_api_keys_non_sequential(self):
        """Test retrieving numbered API keys with gaps in sequence."""
        keys = get_api_keys("anthropic")
        assert len(keys) == 2  # Should only get main-key and key1
        assert keys[0] == "main-key"
        assert keys[1] == "key1"
        # key3 should not be included since key2 is missing

    @patch.dict(os.environ, {})
    def test_get_api_keys_missing(self):
        """Test behavior when no API keys are found."""
        keys = get_api_keys("nonexistent")
        assert len(keys) == 0
        assert isinstance(keys, list)

    @patch.dict(os.environ, {"OPENAI_API_KEY": ""})
    def test_get_api_keys_empty_string(self):
        """Test behavior with empty string API key - should be filtered out."""
        keys = get_api_keys("openai")
        assert len(keys) == 0  # Empty strings are filtered out

    @patch.dict(os.environ, {
        "MISTRAL_API_KEY": "main-key",
        "MISTRAL_API_KEY_1": "",  # Empty string
        "MISTRAL_API_KEY_2": "key2"
    })
    def test_get_api_keys_mixed_empty(self):
        """Test behavior with a mix of valid and empty API keys - stops at empty."""
        keys = get_api_keys("mistral")
        assert len(keys) == 1  # Stops at first empty key
        assert keys[0] == "main-key"