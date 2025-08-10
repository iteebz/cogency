"""Unit tests for Retrieval tool."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from resilient_result import Result

from cogency.storage.vector import VectorStore
from cogency.tools.retrieval import Retrieval


class MockVectorStore(VectorStore):
    """Mock vector store for testing."""

    def __init__(self, mock_results=None):
        self.mock_results = mock_results or []

    async def search(self, query_embedding, top_k=5, filters=None, threshold=None):
        """Return mock search results."""
        return self.mock_results[:top_k]

    async def add(self, embeddings, documents, ids=None):
        return True

    async def delete(self, ids):
        return True


def test_retrieval_init():
    """Test initialization with defaults and custom config."""
    # Defaults (FileStore)
    tool = Retrieval()
    assert tool.name == "retrieval"
    assert tool.embed_model == "openai"
    assert tool.default_top_k == 5

    # Custom vector store
    mock_store = MockVectorStore()
    tool = Retrieval(vector_store=mock_store, embed_model="nomic", top_k=10)
    assert tool.vector_store is mock_store
    assert tool.embed_model == "nomic"
    assert tool.default_top_k == 10


@pytest.mark.asyncio
async def test_run_validation():
    """Test input validation."""
    mock_store = MockVectorStore()
    tool = Retrieval(vector_store=mock_store)

    # Empty query
    result = await tool.run("")
    assert result.failure
    assert "empty" in result.error.lower()

    # Invalid top_k
    result = await tool.run("test", top_k=-1)
    assert result.failure
    assert "positive" in result.error.lower()


@pytest.mark.asyncio
async def test_run_no_results():
    """Test with empty search results."""
    mock_store = MockVectorStore(mock_results=[])
    tool = Retrieval(vector_store=mock_store)

    # Mock embedder
    mock_embedder = AsyncMock()
    mock_embedder.embed.return_value = Result.ok([[0.1, 0.2, 0.3]])
    tool._embedder = mock_embedder

    result = await tool.run("test query")

    assert result.success
    data = result.data
    assert data["total_results"] == 0
    assert data["results"] == []
    assert "No relevant content found" in data["message"]


@pytest.mark.asyncio
async def test_run_successful_search():
    """Test successful search with mock results."""
    mock_results = [
        {
            "content": "Authentication systems are crucial for security",
            "similarity": 0.95,
            "metadata": {"source": "auth.md"},
        },
        {
            "content": "API authentication using tokens",
            "similarity": 0.87,
            "metadata": {"source": "api.md"},
        },
    ]

    mock_store = MockVectorStore(mock_results)
    tool = Retrieval(vector_store=mock_store)

    # Mock embedder
    mock_embedder = AsyncMock()
    mock_embedder.embed.return_value = Result.ok([[0.1, 0.2, 0.3]])
    tool._embedder = mock_embedder

    result = await tool.run("authentication", top_k=2)

    assert result.success
    data = result.data
    assert data["total_results"] == 2
    assert len(data["results"]) == 2

    # Check first result
    first_result = data["results"][0]
    assert first_result["content"] == "Authentication systems are crucial for security"
    assert first_result["similarity_score"] == 0.95
    assert first_result["source"] == "auth.md"

    # Check results summary
    assert "auth.md" in data["results_summary"]
    assert "Found 2 relevant documents" in data["message"]


@pytest.mark.asyncio
async def test_run_with_filters_and_threshold():
    """Test search with filters and threshold parameters."""
    mock_results = [
        {
            "content": "Filtered content",
            "similarity": 0.9,
            "metadata": {"source": "filtered.md", "category": "auth"},
        }
    ]

    mock_store = MockVectorStore(mock_results)
    tool = Retrieval(vector_store=mock_store)

    # Mock embedder
    mock_embedder = AsyncMock()
    mock_embedder.embed.return_value = Result.ok([[0.1, 0.2, 0.3]])
    tool._embedder = mock_embedder

    # Test with filters and threshold
    filters = {"category": "auth"}
    threshold = 0.8

    result = await tool.run("test", top_k=3, filters=filters, threshold=threshold)

    assert result.success
    assert result.data["total_results"] == 1


@pytest.mark.asyncio
async def test_embedding_failure():
    """Test graceful handling of embedding failures."""
    mock_store = MockVectorStore([])
    tool = Retrieval(vector_store=mock_store)

    # Mock embedder that fails
    mock_embedder = AsyncMock()
    mock_embedder.embed.return_value = Result.fail("Embedding failed")
    tool._embedder = mock_embedder

    result = await tool.run("test query")

    assert result.failure
    assert "Query embedding failed" in result.error


@pytest.mark.asyncio
async def test_top_k_capping():
    """Test top_k is capped at reasonable limits."""
    mock_store = MockVectorStore([])
    tool = Retrieval(vector_store=mock_store)

    # Mock embedder
    mock_embedder = AsyncMock()
    mock_embedder.embed.return_value = Result.ok([[0.1, 0.2, 0.3]])
    tool._embedder = mock_embedder

    result = await tool.run("test", top_k=100)

    assert result.success
    # Should be capped at 50 (our new limit)


@pytest.mark.asyncio
async def test_get_embedder_openai():
    """Test embedder setup for OpenAI."""
    tool = Retrieval(embed_model="openai")

    with patch("cogency.providers.setup._setup_embed") as mock_setup:
        mock_embed_class = Mock()
        mock_setup.return_value = mock_embed_class

        await tool._get_embedder()

        mock_setup.assert_called_once_with("openai")
        mock_embed_class.assert_called_once_with()


@pytest.mark.asyncio
async def test_get_embedder_nomic():
    """Test embedder setup for Nomic with task_type."""
    tool = Retrieval(embed_model="nomic")

    with patch("cogency.providers.setup._setup_embed") as mock_setup:
        mock_embed_class = Mock()
        mock_setup.return_value = mock_embed_class

        await tool._get_embedder()

        mock_setup.assert_called_once_with("nomic")
        mock_embed_class.assert_called_once_with(task_type="search_query")
