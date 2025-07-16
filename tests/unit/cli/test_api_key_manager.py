import pytest
from unittest.mock import patch
from cogency.cli.api_key_manager import ApiKeyManager

@pytest.fixture
def mock_get_api_keys():
    with patch('cogency.cli.api_key_manager.get_api_keys') as mock:
        yield mock

def test_get_key_single_key(mock_get_api_keys):
    """Test that get_key returns the single key when only one is available."""
    mock_get_api_keys.return_value = ["test_key_1"]
    manager = ApiKeyManager("test_provider")
    assert manager.get_key() == "test_key_1"
    assert manager.get_key() == "test_key_1"

def test_get_key_multiple_keys(mock_get_api_keys):
    """Test that get_key rotates through the available keys."""
    mock_get_api_keys.return_value = ["test_key_1", "test_key_2", "test_key_3"]
    manager = ApiKeyManager("test_provider")
    assert manager.get_key() == "test_key_1"
    assert manager.get_key() == "test_key_2"
    assert manager.get_key() == "test_key_3"
    assert manager.get_key() == "test_key_1"

def test_get_key_no_keys(mock_get_api_keys):
    """Test that get_key returns None when no keys are available."""
    mock_get_api_keys.return_value = []
    manager = ApiKeyManager("test_provider")
    assert manager.get_key() is None