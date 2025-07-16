import pytest
from unittest.mock import patch, MagicMock, PropertyMock
import os

from cogency.embed.auto import auto_detect_embedder
from cogency.utils.errors import ConfigurationError

@pytest.fixture(autouse=True)
def cleanup_env_vars():
    """Clean up environment variables before each test."""
    original_openai_key = os.getenv("OPENAI_API_KEY")
    original_nomic_key = os.getenv("NOMIC_API_KEY")
    original_openai_key_1 = os.getenv("OPENAI_API_KEY_1")
    original_nomic_key_1 = os.getenv("NOMIC_API_KEY_1")

    if original_openai_key: del os.environ["OPENAI_API_KEY"]
    if original_nomic_key: del os.environ["NOMIC_API_KEY"]
    if original_openai_key_1: del os.environ["OPENAI_API_KEY_1"]
    if original_nomic_key_1: del os.environ["NOMIC_API_KEY_1"]

    yield

    if original_openai_key: os.environ["OPENAI_API_KEY"] = original_openai_key
    if original_nomic_key: os.environ["NOMIC_API_KEY"] = original_nomic_key
    if original_openai_key_1: os.environ["OPENAI_API_KEY_1"] = original_openai_key_1
    if original_nomic_key_1: os.environ["NOMIC_API_KEY_1"] = original_nomic_key_1

# --- Tests for auto_detect_embedder (auto.py) ---

@patch('cogency.embed.auto.OpenAIEmbed')
@patch('cogency.config.get_api_keys', return_value=["test_openai_key"])
def test_auto_detect_embedder_openai(mock_get_api_keys, mock_openai_embed_class):
    """Test auto_detect_embedder prioritizes OpenAI if key is present."""
    mock_openai_embed_instance = MagicMock()
    type(mock_openai_embed_instance).model = PropertyMock(return_value="test-openai-model")
    type(mock_openai_embed_instance).dimensionality = PropertyMock(return_value=1536)
    mock_openai_embed_class.return_value = mock_openai_embed_instance

    embedder = auto_detect_embedder()
    assert embedder is mock_openai_embed_class.return_value
    mock_get_api_keys.assert_called_with("openai")
    mock_openai_embed_class.assert_called_once_with(api_keys=["test_openai_key"])

@patch('cogency.embed.auto.NomicEmbed')
@patch('cogency.embed.auto.OpenAIEmbed')
@patch('cogency.config.get_api_keys', side_effect=[[], ["test_nomic_key"]])
def test_auto_detect_embedder_nomic(mock_get_api_keys, mock_openai_embed_class, mock_nomic_embed_class):
    """Test auto_detect_embedder falls back to Nomic if OpenAI is not present."""
    mock_nomic_embed_instance = MagicMock()
    type(mock_nomic_embed_instance).model = PropertyMock(return_value="test-nomic-model")
    type(mock_nomic_embed_instance).dimensionality = PropertyMock(return_value=768)
    mock_nomic_embed_class.return_value = mock_nomic_embed_instance

    embedder = auto_detect_embedder()
    assert embedder is mock_nomic_embed_class.return_value
    assert mock_get_api_keys.call_args_list[0].args[0] == "openai"
    assert mock_get_api_keys.call_args_list[1].args[0] == "nomic"
    mock_nomic_embed_class.assert_called_once_with(api_keys=["test_nomic_key"])

@patch('cogency.embed.auto.SentenceEmbed')
@patch('cogency.embed.auto.OpenAIEmbed')
@patch('cogency.embed.auto.NomicEmbed')
@patch('cogency.config.get_api_keys', return_value=[])
def test_auto_detect_embedder_sentence(mock_get_api_keys, mock_nomic_embed_class, mock_openai_embed_class, mock_sentence_embed_class):
    """Test auto_detect_embedder falls back to SentenceEmbed if no API keys."""
    mock_sentence_embed_instance = MagicMock()
    type(mock_sentence_embed_instance).model = PropertyMock(return_value="test-sentence-model")
    type(mock_sentence_embed_instance).dimensionality = PropertyMock(return_value=384)
    mock_sentence_embed_class.return_value = mock_sentence_embed_instance

    embedder = auto_detect_embedder()
    assert embedder is mock_sentence_embed_class.return_value
    mock_sentence_embed_class.assert_called_once_with()

@patch('cogency.embed.auto.SentenceEmbed', side_effect=ImportError)
@patch('cogency.embed.auto.OpenAIEmbed')
@patch('cogency.embed.auto.NomicEmbed')
@patch('cogency.config.get_api_keys', return_value=[])
def test_auto_detect_embedder_no_provider(mock_get_api_keys, mock_nomic_embed_class, mock_openai_embed_class, mock_sentence_embed_class):
    """Test auto_detect_embedder raises error if no provider can be found."""
    with pytest.raises(RuntimeError, match="No embedding provider configured"):
        auto_detect_embedder()