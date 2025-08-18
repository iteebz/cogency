"""Search tool tests."""

from unittest.mock import Mock, patch

import pytest

from cogency.tools.search import Search


def test_init():
    """Search initialization with defaults."""
    search = Search()
    assert search.name == "search"
    assert search.max_results == 5
    assert "default 5" in search.description


def test_init_custom():
    """Search initialization with custom max_results."""
    search = Search(max_results=10)
    assert search.max_results == 10
    assert "default 10" in search.description


@pytest.mark.asyncio
async def test_execute_success():
    """Search returns formatted results."""
    search = Search()

    mock_results = [
        {"title": "Python Guide", "body": "Learn Python programming", "href": "https://python.org"},
        {
            "title": "Python Docs",
            "body": "Official documentation",
            "href": "https://docs.python.org",
        },
    ]

    with patch("ddgs.DDGS") as mock_ddgs:
        mock_instance = Mock()
        mock_instance.text.return_value = mock_results
        mock_ddgs.return_value = mock_instance

        result = await search.execute("Python programming")

        assert result.success
        assert "1. Python Guide" in result.unwrap()
        assert "Learn Python programming" in result.unwrap()
        assert "https://python.org" in result.unwrap()
        assert "2. Python Docs" in result.unwrap()
        mock_instance.text.assert_called_once_with("Python programming", max_results=5)


@pytest.mark.asyncio
async def test_execute_empty_query():
    """Search rejects empty query."""
    search = Search()

    result = await search.execute("")

    assert result.failure
    assert "empty" in result.error.lower()


@pytest.mark.asyncio
async def test_execute_no_results():
    """Search handles no results gracefully."""
    search = Search()

    with patch("ddgs.DDGS") as mock_ddgs:
        mock_instance = Mock()
        mock_instance.text.return_value = []
        mock_ddgs.return_value = mock_instance

        result = await search.execute("nonexistent query")

        assert result.success
        assert "No search results found" in result.unwrap()


@pytest.mark.asyncio
async def test_execute_limit_override():
    """Search respects limit parameter override."""
    search = Search(max_results=5)

    with patch("ddgs.DDGS") as mock_ddgs:
        mock_instance = Mock()
        mock_instance.text.return_value = []
        mock_ddgs.return_value = mock_instance

        await search.execute("test", limit=3)

        mock_instance.text.assert_called_once_with("test", max_results=3)


@pytest.mark.asyncio
async def test_execute_limit_cap():
    """Search caps limit at 10."""
    search = Search()

    with patch("ddgs.DDGS") as mock_ddgs:
        mock_instance = Mock()
        mock_instance.text.return_value = []
        mock_ddgs.return_value = mock_instance

        await search.execute("test", limit=20)

        mock_instance.text.assert_called_once_with("test", max_results=10)


@pytest.mark.asyncio
async def test_execute_import_error():
    """Search handles missing dependency."""
    search = Search()

    with patch("builtins.__import__", side_effect=ImportError("No module")):
        result = await search.execute("test")

        assert result.failure
        assert "ddgs" in result.error


@pytest.mark.asyncio
async def test_execute_ddgs_error():
    """Search handles DuckDuckGo API errors."""
    search = Search()

    with patch("ddgs.DDGS") as mock_ddgs:
        mock_instance = Mock()
        mock_instance.text.side_effect = Exception("API Error")
        mock_ddgs.return_value = mock_instance

        result = await search.execute("test")

        assert result.failure
        assert "Search failed" in result.error
        assert "API Error" in result.error
