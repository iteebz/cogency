
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
import numpy as np

from cogency.embed.sentence import SentenceEmbed

# --- Tests for SentenceEmbed (sentence.py) ---

@patch('cogency.embed.sentence.SentenceTransformer')
@patch.object(SentenceEmbed, 'model', new_callable=PropertyMock, return_value="all-MiniLM-L6-v2")
@patch.object(SentenceEmbed, 'dimensionality', new_callable=PropertyMock, return_value=384)
def test_sentence_embed_batch(mock_dimensionality, mock_model, mock_sentence_transformer):
    """Test SentenceEmbed.embed_batch method."""
    mock_model_instance = MagicMock()
    mock_sentence_transformer.return_value = mock_model_instance
    mock_model_instance.encode.return_value = np.array([[0.7, 0.8], [0.9, 0.1]])

    embedder = SentenceEmbed()
    embeddings = embedder.embed_batch(["text1", "text2"])
    assert len(embeddings) == 2
    assert np.array_equal(embeddings[0], np.array([0.7, 0.8]))
    assert np.array_equal(embeddings[1], np.array([0.9, 0.1]))
    mock_model_instance.encode.assert_called_once_with(["text1", "text2"])
