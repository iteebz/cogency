
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
import os
import numpy as np

from cogency.embed.nomic import NomicEmbed

@pytest.fixture(autouse=True)
def cleanup_env_vars():
    """Clean up environment variables before each test."""
    original_nomic_key = os.getenv("NOMIC_API_KEY")
    original_nomic_key_1 = os.getenv("NOMIC_API_KEY_1")

    if original_nomic_key: del os.environ["NOMIC_API_KEY"]
    if original_nomic_key_1: del os.environ["NOMIC_API_KEY_1"]

    yield

    if original_nomic_key: os.environ["NOMIC_API_KEY"] = original_nomic_key
    if original_nomic_key_1: os.environ["NOMIC_API_KEY_1"] = original_nomic_key_1

# --- Tests for NomicEmbed (nomic.py) ---

@patch('cogency.embed.nomic.embed')
@patch.object(NomicEmbed, 'model', new_callable=PropertyMock, return_value="nomic-embed-text-v1.5")
@patch.object(NomicEmbed, 'dimensionality', new_callable=PropertyMock, return_value=768)
def test_nomic_embed_batch(mock_dimensionality, mock_model, mock_nomic_embed):
    """Test NomicEmbed.embed_batch method."""
    mock_nomic_embed.text.return_value = {"embeddings": [[0.3, 0.4], [0.5, 0.6]]}

    embedder = NomicEmbed(api_keys="test_key")
    embeddings = embedder.embed_batch(["text1", "text2"])
    assert len(embeddings) == 2
    assert np.array_equal(embeddings[0], np.array([0.3, 0.4]))
    assert np.array_equal(embeddings[1], np.array([0.5, 0.6]))
    mock_nomic_embed.text.assert_called_once_with(texts=["text1", "text2"], model="nomic-embed-text-v1.5", dimensionality=768)
