"""Unit tests for Retrieval tool."""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import numpy as np
import pytest
from resilient_result import Result

from cogency.tools.retrieval import Retrieval


def test_retrieval_init():
    """Test initialization with defaults and custom config."""
    # Defaults
    tool = Retrieval()
    assert tool.name == "retrieval"
    assert tool.path == Path("./docs")
    assert tool.embed_model == "openai"
    assert tool.default_top_k == 3

    # Custom config
    tool = Retrieval("./knowledge", embed_model="openai", top_k=5)
    assert tool.path == Path("./knowledge")
    assert tool.embed_model == "openai"
    assert tool.default_top_k == 5


@pytest.mark.asyncio
async def test_run_validation():
    """Test input validation."""
    tool = Retrieval("/nonexistent")

    # Empty query
    result = await tool.run("")
    assert result.failure
    assert "empty" in result.error.lower()

    # Invalid top_k
    result = await tool.run("test", top_k=-1)
    assert result.failure
    assert "positive" in result.error.lower()


@pytest.mark.asyncio
async def test_run_no_documents():
    """Test with nonexistent path returns empty results."""
    tool = Retrieval("/nonexistent")
    result = await tool.run("test query")

    assert result.success
    assert result.data["total_results"] == 0
    assert "No documents found" in result.data["message"]


@pytest.mark.asyncio
@patch("cogency.tools.retrieval.Retrieval._get_embedder")
async def test_run_successful_search(mock_get_embedder, temp_docs_dir):
    """Test successful end-to-end search."""
    mock_embedder = Mock()
    mock_embedder.embed = Mock(
        side_effect=[
            Result.ok([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]]),  # Doc embeddings
            Result.ok([[0.1, 0.2, 0.3]]),  # Query embedding (matches first doc)
        ]
    )
    mock_get_embedder.return_value = mock_embedder

    tool = Retrieval(path=str(temp_docs_dir))
    result = await tool.run("authentication")

    assert result.success
    assert result.data["total_results"] > 0
    assert "results" in result.data


def test_document_discovery(temp_docs_dir):
    """Test document discovery and chunking."""
    tool = Retrieval(path=str(temp_docs_dir))

    # Discovery
    documents = tool._discover_documents()
    assert len(documents) == 3
    assert all(doc.suffix == ".md" for doc in documents)

    # Chunking
    content = "Short content for testing chunking functionality in the retrieval system."
    chunks = tool._chunk_document(content, "test.md")
    assert len(chunks) == 1
    assert chunks[0]["content"] == content
    assert chunks[0]["source"] == "test.md"


@pytest.mark.asyncio
async def test_index_management(temp_docs_dir):
    """Test lazy index building and change detection."""
    tool = Retrieval(path=str(temp_docs_dir))

    # Initial hash
    hash1 = tool._compute_content_hash()
    assert hash1

    # Hash consistency
    hash2 = tool._compute_content_hash()
    assert hash1 == hash2

    # Hash changes with content
    (temp_docs_dir / "new.md").write_text("New content")
    hash3 = tool._compute_content_hash()
    assert hash3 != hash1


@pytest.mark.asyncio
async def test_search_functionality():
    """Test semantic search with mock data."""
    tool = Retrieval()
    tool._index = {
        "chunks": [
            {"content": "authentication system", "source": "auth.md", "start": 0, "end": 20},
            {"content": "API documentation", "source": "api.md", "start": 0, "end": 17},
        ],
        "embeddings": np.array(
            [
                [0.9, 0.1],  # High similarity to query
                [0.1, 0.9],  # Low similarity to query
            ]
        ),
    }
    tool._embedder = Mock()
    tool._embedder.embed = Mock(return_value=Result.ok([[1.0, 0.0]]))  # Perfect match to first

    results = await tool._search("auth", 1)

    assert len(results) == 1
    assert results[0]["source"] == "auth.md"
    assert results[0]["similarity_score"] > 0.5


@pytest.mark.asyncio
@patch("cogency.providers.setup._setup_embed")
async def test_provider_integration(mock_setup_embed):
    """Test canonical provider setup integration."""
    mock_embed_class = Mock()
    mock_embed_instance = Mock()
    mock_embed_class.return_value = mock_embed_instance
    mock_setup_embed.return_value = mock_embed_class

    tool = Retrieval(embed_model="openai")
    embedder = await tool._get_embedder()

    mock_setup_embed.assert_called_once_with("openai")
    assert embedder is mock_embed_instance


@pytest.mark.asyncio
async def test_top_k_capping(temp_docs_dir):
    """Test top_k is capped at reasonable limits."""
    tool = Retrieval(path=str(temp_docs_dir))
    tool._index = {"chunks": [], "embeddings": []}

    with patch.object(tool, "_ensure_index"), patch.object(tool, "_search") as mock_search:
        mock_search.return_value = []
        await tool.run("test", top_k=100)
        mock_search.assert_called_once_with("test", 20)  # Capped at 20


@pytest.mark.asyncio
async def test_error_handling(temp_docs_dir):
    """Test graceful error handling."""
    tool = Retrieval(path=str(temp_docs_dir))
    tool._embedder = Mock()
    tool._embedder.embed = Mock(side_effect=Exception("Embedding failed"))

    # Should handle embedding failures gracefully
    await tool._build_index()
    assert tool._index is None
