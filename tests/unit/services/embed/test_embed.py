"""Embedding service tests."""

import pytest

from cogency.services.embed.base import BaseEmbed
from cogency.utils.results import Result


class MockEmbedder(BaseEmbed):
    """Mock embedder for testing."""

    def __init__(self, dimension=384):
        super().__init__()
        self.dimension = dimension

    def embed(self, text):
        """Mock embed method - handles both string and list[str]."""
        if isinstance(text, str):
            return Result.ok([[0.1, 0.2, 0.3] * (self.dimension // 3)])
        return Result.ok([[0.1, 0.2, 0.3] * (self.dimension // 3) for _ in text])

    @property
    def model(self):
        return "mock-model"

    @property
    def dimensionality(self):
        return self.dimension


def test_abstract():
    with pytest.raises(TypeError):
        BaseEmbed()


def test_single():
    embedder = MockEmbedder()
    result = embedder.embed("test text")

    assert result.success
    assert len(result.data) == 1
    assert len(result.data[0]) == 384


def test_multiple():
    embedder = MockEmbedder()
    texts = ["first", "second", "third"]
    result = embedder.embed(texts)

    assert result.success
    assert len(result.data) == 3


def test_properties():
    embedder = MockEmbedder(dimension=512)
    assert embedder.model == "mock-model"
    assert embedder.dimensionality == 512
