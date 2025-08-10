"""Unit tests for FileStore vector storage."""

import json
import tempfile
from pathlib import Path

import pytest

from cogency.storage.vector import FileStore


@pytest.fixture
def sample_embeddings():
    """Sample embeddings data for testing."""
    return {
        "embeddings": [
            [0.1, 0.2, 0.3],  # doc 1
            [0.4, 0.5, 0.6],  # doc 2
            [0.1, 0.2, 0.4],  # doc 3 (similar to doc 1)
        ],
        "documents": [
            {
                "content": "Machine learning is a subset of AI",
                "metadata": {"source": "doc1.txt", "category": "ai"},
            },
            {
                "content": "Natural language processing uses neural networks",
                "metadata": {"source": "doc2.txt", "category": "nlp"},
            },
            {
                "content": "Machine learning algorithms learn from data",
                "metadata": {"source": "doc3.txt", "category": "ai"},
            },
        ],
    }


@pytest.fixture
def embeddings_file(sample_embeddings):
    """Create temporary embeddings file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(sample_embeddings, f)
        f.flush()  # Ensure data is written
        temp_path = f.name

    yield temp_path
    Path(temp_path).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_file_store_search_basic(embeddings_file):
    """Test basic search functionality."""
    store = FileStore(embeddings_file)

    # Query similar to doc 1: [0.1, 0.2, 0.3]
    query_embedding = [0.1, 0.2, 0.35]

    results = await store.search(query_embedding, top_k=2)

    assert len(results) == 2

    # Should return most similar documents (order may vary based on cosine similarity)
    contents = [result["content"] for result in results]
    assert (
        "Machine learning is a subset of AI" in contents
        or "Machine learning algorithms learn from data" in contents
    )
    assert results[0]["similarity"] > results[1]["similarity"]
    assert "source" in results[0]["metadata"]


@pytest.mark.asyncio
async def test_file_store_search_with_filters(embeddings_file):
    """Test search with metadata filters."""
    store = FileStore(embeddings_file)

    query_embedding = [0.1, 0.2, 0.35]
    filters = {"category": "ai"}

    results = await store.search(query_embedding, top_k=3, filters=filters)

    # Should only return AI-related docs (doc1 and doc3)
    assert len(results) == 2
    for result in results:
        assert result["metadata"]["category"] == "ai"


@pytest.mark.asyncio
async def test_file_store_search_with_threshold(embeddings_file):
    """Test search with similarity threshold."""
    store = FileStore(embeddings_file)

    # Query very different from all documents - use much lower threshold
    query_embedding = [1.0, 1.0, 1.0]
    threshold = 0.99  # Very high threshold to ensure no matches

    results = await store.search(query_embedding, top_k=3, threshold=threshold)

    # Should return no results due to high similarity threshold
    assert len(results) == 0


@pytest.mark.asyncio
async def test_file_store_nonexistent_file():
    """Test handling of nonexistent file."""
    store = FileStore("nonexistent.json")

    with pytest.raises(FileNotFoundError):
        await store.search([0.1, 0.2, 0.3])


@pytest.mark.asyncio
async def test_file_store_add_not_implemented(embeddings_file):
    """Test that add operations are not implemented (read-only)."""
    store = FileStore(embeddings_file)

    with pytest.raises(NotImplementedError):
        await store.add([[0.1, 0.2]], [{"content": "test"}])


@pytest.mark.asyncio
async def test_file_store_delete_not_implemented(embeddings_file):
    """Test that delete operations are not implemented (read-only)."""
    store = FileStore(embeddings_file)

    with pytest.raises(NotImplementedError):
        await store.delete(["doc1"])


def test_file_store_invalid_format():
    """Test handling of invalid embeddings file format."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"invalid": "format"}, f)
        file_path = f.name

    store = FileStore(file_path)

    with pytest.raises(ValueError, match="Invalid embeddings file format"):
        import asyncio

        asyncio.run(store.search([0.1, 0.2, 0.3]))

    Path(file_path).unlink()
