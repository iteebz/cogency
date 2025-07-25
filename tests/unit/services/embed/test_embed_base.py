"""Test BaseEmbed business logic."""

import numpy as np
import pytest

from cogency.services.embed.base import BaseEmbed
from cogency.utils.results import Result


class MockEmbed(BaseEmbed):
    """Test embedding implementation."""

    def __init__(self, api_key="test-key", model_name="text-embedding-3-small", dims=1536):
        super().__init__(api_key)
        self._model = model_name
        self._dims = dims

    def embed_one(self, text: str, **kwargs) -> Result:
        length = len(text) if text else 1
        embedding = np.full(self._dims, length / 100.0, dtype=np.float32)
        return Result.ok(embedding)

    def embed_many(self, texts: list[str], **kwargs) -> Result:
        embeddings = []
        for text in texts:
            result = self.embed_one(text, **kwargs)
            if not result.success:
                return result
            embeddings.append(result.data)
        return Result.ok(embeddings)

    @property
    def model(self) -> str:
        return self._model

    @property
    def dimensionality(self) -> int:
        return self._dims


def test_base_embed_abstract():
    """Test abstract base class."""
    with pytest.raises(TypeError):
        BaseEmbed("test-key")


def test_embed_one():
    """Test single text embedding."""
    embed = MockEmbed()
    result = embed.embed_one("Hello world")

    assert result.success
    embedding = result.data
    assert isinstance(embedding, np.ndarray)
    assert embedding.shape == (1536,)
    assert embedding.dtype == np.float32


def test_embed_many():
    """Test multiple text embeddings."""
    embed = MockEmbed()
    texts = ["Hello", "world", "test"]
    result = embed.embed_many(texts)

    assert result.success
    embeddings = result.data
    assert len(embeddings) == 3
    assert all(isinstance(r, np.ndarray) for r in embeddings)
    assert all(r.shape == (1536,) for r in embeddings)


def test_embed_array():
    """Test array conversion."""
    embed = MockEmbed()
    texts = ["text1", "text2", "text3"]
    result = embed.embed_array(texts)

    assert result.success
    assert isinstance(result.data, np.ndarray)
    assert result.data.shape == (3, 1536)
    assert result.data.dtype == np.float32


def test_properties():
    """Test model properties."""
    embed = MockEmbed(model_name="custom-model", dims=768)
    assert embed.model == "custom-model"
    assert embed.dimensionality == 768
