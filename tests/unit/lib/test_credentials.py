"""Test credential detection."""

import os
from unittest.mock import mock_open, patch


def test_detect_api_key_from_env():
    """Detect API key from environment variables."""
    from cogency.lib.credentials import detect_api_key

    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test123"}):
        key = detect_api_key("openai")
        assert key == "sk-test123"


def test_detect_api_key_patterns():
    """Test different API key naming patterns."""
    from cogency.lib.credentials import detect_api_key

    # Test UPPERCASE_API_KEY pattern
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test"}):
        key = detect_api_key("anthropic")
        assert key == "sk-ant-test"

    # Test SERVICE_KEY pattern
    with patch.dict(os.environ, {"GEMINI_KEY": "gg-test"}):
        key = detect_api_key("gemini")
        assert key == "gg-test"


def test_detect_api_key_gemini_google_mapping():
    """Test Gemini's GOOGLE_API_KEY mapping."""
    from cogency.lib.credentials import detect_api_key

    # Test GOOGLE_API_KEY maps to gemini
    with patch.dict(os.environ, {"GOOGLE_API_KEY": "google-test-key"}):
        key = detect_api_key("gemini")
        assert key == "google-test-key"

    # Test precedence: GEMINI_API_KEY takes priority over GOOGLE_API_KEY
    with patch.dict(os.environ, {"GEMINI_API_KEY": "gemini-key", "GOOGLE_API_KEY": "google-key"}):
        key = detect_api_key("gemini")
        assert key == "gemini-key"


def test_detect_api_key_not_found():
    """Return None when API key not found."""
    from cogency.lib.credentials import detect_api_key

    # Clear any existing keys
    with patch.dict(os.environ, {}, clear=True):
        key = detect_api_key("nonexistent")
        assert key is None


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data="OPENAI_API_KEY=sk-from-env\nANTHROPIC_API_KEY=sk-ant-env",
)
@patch("pathlib.Path.exists", return_value=True)
def test_load_env_file(mock_exists, mock_file):
    """Load API keys from .env file."""
    from cogency.lib.credentials import load_env

    # Clear environment first
    with patch.dict(os.environ, {}, clear=True):
        load_env()

        # Check that environment was updated
        assert "OPENAI_API_KEY" in os.environ
        assert os.environ["OPENAI_API_KEY"] == "sk-from-env"
