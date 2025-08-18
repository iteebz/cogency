"""Retrieve tool tests."""

from unittest.mock import patch

import pytest

from cogency.tools.retrieve import Retrieve


def test_init():
    """Retrieve initialization."""
    tool = Retrieve()
    assert tool.name == "retrieve"
    assert "search knowledge" in tool.description.lower()
    assert "max 5" in tool.description


@pytest.mark.asyncio
async def test_execute_success():
    """Retrieve returns formatted results."""
    tool = Retrieve()

    mock_results = [
        {"doc_id": "doc1", "content": "Python is a programming language", "relevance": 0.95},
        {
            "doc_id": "doc2",
            "content": "Python has many libraries for data science",
            "relevance": 0.87,
        },
    ]

    with patch("cogency.tools.retrieve.search_documents", return_value=mock_results):
        result = await tool.execute("Python programming")

        assert result.success
        assert "Found 2 documents" in result.unwrap()
        assert "doc1" in result.unwrap()
        assert "doc2" in result.unwrap()
        assert "Python is a programming" in result.unwrap()
        assert "relevance: 0.95" in result.unwrap()


@pytest.mark.asyncio
async def test_execute_no_results():
    """Retrieve handles no search results."""
    tool = Retrieve()

    with patch("cogency.tools.retrieve.search_documents", return_value=[]):
        result = await tool.execute("nonexistent query")

        assert result.success
        assert "No documents found" in result.unwrap()
        assert "nonexistent query" in result.unwrap()


@pytest.mark.asyncio
async def test_execute_with_limit():
    """Retrieve respects limit parameter."""
    tool = Retrieve()

    with patch("cogency.tools.retrieve.search_documents") as mock_search:
        mock_search.return_value = []

        await tool.execute("test query", limit=2)

        mock_search.assert_called_once_with("test query", 2)


@pytest.mark.asyncio
async def test_execute_limit_cap():
    """Retrieve caps limit at 5."""
    tool = Retrieve()

    with patch("cogency.tools.retrieve.search_documents") as mock_search:
        mock_search.return_value = []

        await tool.execute("test query", limit=10)

        mock_search.assert_called_once_with("test query", 5)


@pytest.mark.asyncio
async def test_execute_default_limit():
    """Retrieve uses default limit."""
    tool = Retrieve()

    with patch("cogency.tools.retrieve.search_documents") as mock_search:
        mock_search.return_value = []

        await tool.execute("test query")

        mock_search.assert_called_once_with("test query", 3)


@pytest.mark.asyncio
async def test_execute_truncates_content():
    """Retrieve truncates long document content."""
    tool = Retrieve()

    long_content = "A" * 300  # Longer than 200 char limit
    mock_results = [{"doc_id": "doc1", "content": long_content, "relevance": 0.9}]

    with patch("cogency.tools.retrieve.search_documents", return_value=mock_results):
        result = await tool.execute("test")

        assert result.success
        assert "..." in result.unwrap()  # Should be truncated
        assert len(result.unwrap()) < len(long_content) + 100  # Much shorter than original


@pytest.mark.asyncio
async def test_execute_search_error():
    """Retrieve handles search backend errors."""
    tool = Retrieve()

    with patch(
        "cogency.tools.retrieve.search_documents", side_effect=Exception("Search backend error")
    ):
        result = await tool.execute("test")

        assert result.failure
        assert "Retrieve error" in result.error
        assert "Search backend error" in result.error


@pytest.mark.asyncio
async def test_execute_multiple_results_formatting():
    """Retrieve formats multiple results correctly."""
    tool = Retrieve()

    mock_results = [
        {"doc_id": "first", "content": "First document", "relevance": 0.9},
        {"doc_id": "second", "content": "Second document", "relevance": 0.8},
        {"doc_id": "third", "content": "Third document", "relevance": 0.7},
    ]

    with patch("cogency.tools.retrieve.search_documents", return_value=mock_results):
        result = await tool.execute("test")

        assert result.success
        assert "1. first" in result.unwrap()
        assert "2. second" in result.unwrap()
        assert "3. third" in result.unwrap()
        assert "Found 3 documents" in result.unwrap()
