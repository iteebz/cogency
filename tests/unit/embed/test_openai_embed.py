
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
import os
import numpy as np

from cogency.embed.openai import OpenAIEmbed

@pytest.fixture(autouse=True)
def cleanup_env_vars():
    """Clean up environment variables before each test."""
    original_openai_key = os.getenv("OPENAI_API_KEY")
    original_openai_key_1 = os.getenv("OPENAI_API_KEY_1")

    if original_openai_key: del os.environ["OPENAI_API_KEY"]
    if original_openai_key_1: del os.environ["OPENAI_API_KEY_1"]

    yield

    if original_openai_key: os.environ["OPENAI_API_KEY"] = original_openai_key
    if original_openai_key_1: os.environ["OPENAI_API_KEY_1"] = original_openai_key_1

# --- Tests for OpenAIEmbed (openai.py) ---

@patch('openai.OpenAI')
@patch.object(OpenAIEmbed, 'model', new_callable=PropertyMock, return_value="text-embedding-3-small")
@patch.object(OpenAIEmbed, 'dimensionality', new_callable=PropertyMock, return_value=1536)
def test_openai_embed_single(mock_dimensionality, mock_model, mock_openai):
    """Test OpenAIEmbed.embed_single method."""
    mock_client_instance = MagicMock()
    mock_openai.return_value = mock_client_instance
    mock_client_instance.embeddings.create.return_value.data = [MagicMock(embedding=[0.1, 0.2])]

    embedder = OpenAIEmbed(api_keys="test_key")
    embedding = embedder.embed_single("test text")
    assert np.array_equal(embedding, np.array([0.1, 0.2]))
    mock_client_instance.embeddings.create.assert_called_once_with(input="test text", model="text-embedding-3-small")

@patch('openai.OpenAI')
@patch.object(OpenAIEmbed, 'model', new_callable=PropertyMock, return_value="text-embedding-3-small")
@patch.object(OpenAIEmbed, 'dimensionality', new_callable=PropertyMock, return_value=1536)
def test_openai_embed_batch(mock_dimensionality, mock_model, mock_openai):
    """Test OpenAIEmbed.embed_batch method."""
    mock_client_instance = MagicMock()
    mock_openai.return_value = mock_client_instance
    mock_client_instance.embeddings.create.return_value.data = [MagicMock(embedding=[0.1, 0.2]), MagicMock(embedding=[0.3, 0.4])]

    embedder = OpenAIEmbed(api_keys="test_key")
    embeddings = embedder.embed_batch(["text1", "text2"])
    assert len(embeddings) == 2
    assert np.array_equal(embeddings[0], np.array([0.1, 0.2]))
    assert np.array_equal(embeddings[1], np.array([0.3, 0.4]))
    mock_client_instance.embeddings.create.assert_called_once_with(input=["text1", "text2"], model="text-embedding-3-small")
