"""Tests for configuration management."""

import os
from unittest.mock import patch

import pytest

from cogency.config import Config, get_config, load_api_keys


class TestLoadApiKeys:
    """Test suite for API key loading."""

    @patch.dict(os.environ, {}, clear=True)
    def test_load_api_keys_empty(self):
        """Test loading API keys when none are set."""
        keys = load_api_keys()
        assert keys == []

    @patch.dict(os.environ, {"GEMINI_API_KEY": "single-key"}, clear=True)
    def test_load_api_keys_single(self):
        """Test loading single API key."""
        keys = load_api_keys()
        assert keys == ["single-key"]

    @patch.dict(
        os.environ,
        {"GEMINI_API_KEY_1": "key-1", "GEMINI_API_KEY_2": "key-2", "GEMINI_API_KEY_3": "key-3"},
        clear=True,
    )
    def test_load_api_keys_numbered(self):
        """Test loading numbered API keys."""
        keys = load_api_keys()
        assert keys == ["key-1", "key-2", "key-3"]

    @patch.dict(
        os.environ,
        {
            "GEMINI_API_KEY_1": "key-1",
            "GEMINI_API_KEY_3": "key-3",  # Skip key-2
            "GEMINI_API_KEY": "fallback-key",
        },
        clear=True,
    )
    def test_load_api_keys_numbered_gaps(self):
        """Test loading numbered API keys with gaps."""
        keys = load_api_keys()
        # Should only get key-1, not key-3 since key-2 is missing
        assert keys == ["key-1"]

    @patch.dict(
        os.environ,
        {
            "GEMINI_API_KEY_1": "  key-with-spaces  ",
            "GEMINI_API_KEY_2": "",  # Empty key
            "GEMINI_API_KEY_3": "   ",  # Whitespace only
        },
        clear=True,
    )
    def test_load_api_keys_whitespace_handling(self):
        """Test loading API keys with whitespace."""
        keys = load_api_keys()
        # Should strip whitespace and skip empty keys
        assert keys == ["key-with-spaces"]

    @patch.dict(
        os.environ,
        {"GEMINI_API_KEY": "fallback-key", "GEMINI_API_KEY_1": "numbered-key"},
        clear=True,
    )
    def test_load_api_keys_numbered_priority(self):
        """Test that numbered keys take priority over single key."""
        keys = load_api_keys()
        assert keys == ["numbered-key"]


class TestConfig:
    """Test suite for Config dataclass."""

    def test_config_defaults(self):
        """Test Config default values."""
        config = Config(api_keys=["test-key"])

        assert config.api_keys == ["test-key"]
        assert config.model == "gemini-2.5-flash"
        assert config.timeout == 15.0
        assert config.temperature == 0.7
        assert config.agent_name == "CogencyAgent"
        assert config.max_depth == 10
        assert config.file_base_dir == "workspace"
        assert config.web_max_results == 5
        assert config.web_rate_limit == 1.0

    def test_config_custom_values(self):
        """Test Config with custom values."""
        config = Config(
            api_keys=["key1", "key2"],
            model="custom-model",
            timeout=30.0,
            temperature=0.5,
            agent_name="CustomAgent",
            max_depth=20,
            file_base_dir="/custom/workspace",
            web_max_results=10,
            web_rate_limit=2.0,
        )

        assert config.api_keys == ["key1", "key2"]
        assert config.model == "custom-model"
        assert config.timeout == 30.0
        assert config.temperature == 0.5
        assert config.agent_name == "CustomAgent"
        assert config.max_depth == 20
        assert config.file_base_dir == "/custom/workspace"
        assert config.web_max_results == 10
        assert config.web_rate_limit == 2.0


class TestGetConfig:
    """Test suite for get_config function."""

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}, clear=True)
    @patch("cogency.config.find_dotenv")
    @patch("cogency.config.load_dotenv")
    def test_get_config_basic(self, mock_load_dotenv, mock_find_dotenv):
        """Test basic config loading."""
        mock_find_dotenv.return_value = None

        config = get_config()

        assert config.api_keys == ["test-key"]
        assert config.model == "gemini-2.5-flash"

    @patch.dict(os.environ, {}, clear=True)
    @patch("cogency.config.find_dotenv")
    def test_get_config_no_api_keys(self, mock_find_dotenv):
        """Test config loading with no API keys."""
        mock_find_dotenv.return_value = None

        with pytest.raises(ValueError, match="No API keys found"):
            get_config()

    @patch.dict(
        os.environ,
        {
            "GEMINI_API_KEY": "test-key",
            "COGENCY_MODEL": "custom-model",
            "COGENCY_TIMEOUT": "25.5",
            "COGENCY_TEMPERATURE": "0.8",
            "COGENCY_AGENT_NAME": "TestAgent",
            "COGENCY_MAX_DEPTH": "15",
            "COGENCY_FILE_BASE_DIR": "/test/workspace",
            "COGENCY_WEB_MAX_RESULTS": "8",
            "COGENCY_WEB_RATE_LIMIT": "1.5",
        },
        clear=True,
    )
    @patch("cogency.config.find_dotenv")
    @patch("cogency.config.load_dotenv")
    def test_get_config_custom_env_vars(self, mock_load_dotenv, mock_find_dotenv):
        """Test config loading with custom environment variables."""
        mock_find_dotenv.return_value = None

        config = get_config()

        assert config.api_keys == ["test-key"]
        assert config.model == "custom-model"
        assert config.timeout == 25.5
        assert config.temperature == 0.8
        assert config.agent_name == "TestAgent"
        assert config.max_depth == 15
        assert config.file_base_dir == "/test/workspace"
        assert config.web_max_results == 8
        assert config.web_rate_limit == 1.5

    @patch.dict(
        os.environ,
        {
            "GEMINI_API_KEY": "test-key",
            "COGENCY_TIMEOUT": "invalid-float",
        },
        clear=True,
    )
    @patch("cogency.config.find_dotenv")
    def test_get_config_invalid_float(self, mock_find_dotenv):
        """Test config loading with invalid float values."""
        mock_find_dotenv.return_value = None

        with pytest.raises(ValueError):
            get_config()

    @patch.dict(
        os.environ,
        {
            "GEMINI_API_KEY": "test-key",
            "COGENCY_MAX_DEPTH": "invalid-int",
        },
        clear=True,
    )
    @patch("cogency.config.find_dotenv")
    def test_get_config_invalid_int(self, mock_find_dotenv):
        """Test config loading with invalid integer values."""
        mock_find_dotenv.return_value = None

        with pytest.raises(ValueError):
            get_config()

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}, clear=True)
    @patch("cogency.config.find_dotenv")
    @patch("cogency.config.load_dotenv")
    def test_get_config_with_dotenv(self, mock_load_dotenv, mock_find_dotenv):
        """Test config loading with .env file."""
        mock_find_dotenv.return_value = "/path/to/.env"

        config = get_config()

        mock_find_dotenv.assert_called_once_with(usecwd=True)
        mock_load_dotenv.assert_called_once_with("/path/to/.env")
        assert config.api_keys == ["test-key"]

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}, clear=True)
    @patch("cogency.config.find_dotenv")
    @patch("cogency.config.load_dotenv")
    def test_get_config_no_dotenv(self, mock_load_dotenv, mock_find_dotenv):
        """Test config loading without .env file."""
        mock_find_dotenv.return_value = None

        config = get_config()

        mock_find_dotenv.assert_called_once_with(usecwd=True)
        mock_load_dotenv.assert_not_called()
        assert config.api_keys == ["test-key"]
