"""Test BaseEmbed business logic."""
import pytest
import numpy as np

from cogency.embed.base import BaseEmbed


class MockEmbed(BaseEmbed):
    """Test embedding implementation."""
    
    def __init__(self, api_key="test-key", model_name="text-embedding-3-small", dims=1536):
        super().__init__(api_key)
        self._model = model_name
        self._dims = dims
    
    def embed_one(self, text: str, **kwargs) -> np.ndarray:
        length = len(text) if text else 1
        return np.full(self._dims, length / 100.0, dtype=np.float32)
    
    def embed_many(self, texts: list[str], **kwargs) -> list[np.ndarray]:
        return [self.embed_one(text, **kwargs) for text in texts]
    
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
    
    assert isinstance(result, np.ndarray)
    assert result.shape == (1536,)
    assert result.dtype == np.float32


def test_embed_many():
    """Test multiple text embeddings."""
    embed = MockEmbed()
    texts = ["Hello", "world", "test"]
    results = embed.embed_many(texts)
    
    assert len(results) == 3
    assert all(isinstance(r, np.ndarray) for r in results)
    assert all(r.shape == (1536,) for r in results)


def test_embed_array():
    """Test array conversion."""
    embed = MockEmbed()
    texts = ["text1", "text2", "text3"]
    result = embed.embed_array(texts)
    
    assert isinstance(result, np.ndarray)
    assert result.shape == (3, 1536)
    assert result.dtype == np.float32


def test_properties():
    """Test model properties."""
    embed = MockEmbed(model_name="custom-model", dims=768)
    assert embed.model == "custom-model"
    assert embed.dimensionality == 768