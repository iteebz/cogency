"""Semantic search business logic tests."""

import json
import tempfile
from unittest.mock import AsyncMock, Mock

import pytest
from resilient_result import Result

from cogency.semantic import rank, search_json_index, search_sqlite_vectors, semantic_search


def test_rank_filters_by_threshold():
    """Test ranking filters results by similarity threshold."""
    results = [
        {"content": "high", "similarity": 0.9},
        {"content": "medium", "similarity": 0.5},
        {"content": "low", "similarity": 0.2},
    ]

    ranked = rank(results, top_k=10, threshold=0.4)
    assert len(ranked) == 2
    assert ranked[0]["content"] == "high"
    assert ranked[1]["content"] == "medium"


def test_rank_sorts_by_similarity():
    """Test ranking sorts by similarity descending."""
    results = [
        {"content": "medium", "similarity": 0.5},
        {"content": "high", "similarity": 0.9},
        {"content": "low", "similarity": 0.3},
    ]

    ranked = rank(results, top_k=10, threshold=0.0)
    assert ranked[0]["similarity"] == 0.9
    assert ranked[1]["similarity"] == 0.5
    assert ranked[2]["similarity"] == 0.3


def test_rank_respects_top_k():
    """Test ranking respects top_k limit."""
    results = [{"content": f"doc{i}", "similarity": 0.9 - i * 0.1} for i in range(10)]

    ranked = rank(results, top_k=3, threshold=0.0)
    assert len(ranked) == 3
    assert ranked[0]["similarity"] == 0.9
    assert ranked[2]["similarity"] == 0.7


@pytest.mark.asyncio
async def test_search_json_index_file_not_found():
    """Test JSON search handles missing files gracefully."""
    result = await search_json_index([0.1] * 384, "/nonexistent/file.json")
    assert result.failure
    assert "not found" in result.error


@pytest.mark.asyncio
async def test_search_json_index_empty_embeddings():
    """Test JSON search handles empty embeddings."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"embeddings": [], "documents": []}, f)
        f.flush()

        result = await search_json_index([0.1] * 384, f.name)
        assert result.success
        assert result.data == []


@pytest.mark.asyncio
async def test_search_json_index_length_mismatch():
    """Test JSON search validates embedding/document length."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(
            {"embeddings": [[0.1] * 384], "documents": [{"content": "doc1"}, {"content": "doc2"}]},
            f,
        )
        f.flush()

        result = await search_json_index([0.1] * 384, f.name)
        assert result.failure
        assert "length mismatch" in result.error


@pytest.mark.asyncio
async def test_search_json_index_success():
    """Test successful JSON search with vectorized computation."""
    # Create test data
    query_embedding = [1.0, 0.0, 0.0]
    doc1_embedding = [1.0, 0.0, 0.0]  # Perfect match
    doc2_embedding = [0.0, 1.0, 0.0]  # No match

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(
            {
                "embeddings": [doc1_embedding, doc2_embedding],
                "documents": [
                    {"content": "Perfect match", "metadata": {"type": "test"}},
                    {"content": "No match", "metadata": {"type": "other"}},
                ],
            },
            f,
        )
        f.flush()

        result = await search_json_index(query_embedding, f.name, top_k=2, threshold=0.5)
        assert result.success
        assert len(result.data) == 1
        assert result.data[0]["content"] == "Perfect match"
        assert result.data[0]["similarity"] > 0.9


@pytest.mark.asyncio
async def test_search_json_index_metadata_filters():
    """Test JSON search applies metadata filters correctly."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(
            {
                "embeddings": [[1.0, 0.0], [0.9, 0.1]],
                "documents": [
                    {"content": "Type A doc", "metadata": {"type": "A", "source": "test"}},
                    {"content": "Type B doc", "metadata": {"type": "B", "source": "test"}},
                ],
            },
            f,
        )
        f.flush()

        result = await search_json_index([1.0, 0.0], f.name, filters={"type": "A"})
        assert result.success
        assert len(result.data) == 1
        assert result.data[0]["content"] == "Type A doc"


@pytest.mark.asyncio
async def test_search_sqlite_vectors_no_results():
    """Test SQLite search handles empty results."""
    mock_connection = Mock()
    mock_cursor = Mock()
    mock_cursor.fetchall.return_value = []
    mock_connection.cursor.return_value = mock_cursor

    result = await search_sqlite_vectors([0.1] * 384, mock_connection, "user123")
    assert result.success
    assert result.data == []


@pytest.mark.asyncio
async def test_search_sqlite_vectors_success():
    """Test successful SQLite vector search."""
    mock_connection = Mock()
    mock_cursor = Mock()
    mock_cursor.fetchall.return_value = [
        ("content1", '{"type": "doc"}', "[1.0, 0.0]"),
        ("content2", '{"type": "other"}', "[0.0, 1.0]"),
    ]
    mock_connection.cursor.return_value = mock_cursor

    # Query embedding that matches first document
    result = await search_sqlite_vectors([1.0, 0.0], mock_connection, "user123", top_k=1)
    assert result.success
    assert len(result.data) == 1
    assert result.data[0]["content"] == "content1"


@pytest.mark.asyncio
async def test_semantic_search_missing_parameters():
    """Test universal search requires proper parameters."""
    mock_embedder = AsyncMock()
    mock_embedder.embed.return_value = Result.ok([[0.1] * 384])

    result = await semantic_search(mock_embedder, "test query")
    assert result.failure
    assert "Must provide either file_path or db_connection" in result.error


@pytest.mark.asyncio
async def test_semantic_search_embedding_failure():
    """Test universal search handles embedding failures."""
    mock_embedder = AsyncMock()
    mock_embedder.embed.return_value = Result.fail("Embedding service down")

    result = await semantic_search(mock_embedder, "test query", file_path="test.json")
    assert result.failure
    assert "Query embedding failed" in result.error


@pytest.mark.asyncio
async def test_semantic_search_json_delegation():
    """Test universal search delegates to JSON search correctly."""
    mock_embedder = AsyncMock()
    mock_embedder.embed.return_value = Result.ok([[0.1] * 384])

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"embeddings": [], "documents": []}, f)
        f.flush()

        result = await semantic_search(mock_embedder, "test query", file_path=f.name, top_k=5)
        assert result.success
        assert result.data == []
