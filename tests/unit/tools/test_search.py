"""Search tool tests."""

import pytest

from cogency.tools.search import Search


@pytest.mark.asyncio
async def test_success(mock_search_engine):
    """Test successful search execution."""
    mock_ddgs, _ = mock_search_engine
    tool = Search()
    mock_results = [{"title": "Test", "href": "https://example.com", "body": "Content"}]
    mock_ddgs.return_value.text.return_value = mock_results

    result = await tool.run(query="test query")
    assert result.success
    assert result.unwrap()["total_found"] == 1
    assert result.unwrap()["query"] == "test query"
    assert len(result.unwrap()["results"]) == 1
    assert result.unwrap()["results"][0]["title"] == "Test"


@pytest.mark.asyncio
async def test_no_results(mock_search_engine):
    """Test search with no results."""
    mock_ddgs, _ = mock_search_engine
    tool = Search()
    mock_ddgs.return_value.text.return_value = []

    result = await tool.run(query="no results")
    assert result.success
    assert result.unwrap()["total_found"] == 0
    assert result.unwrap()["results"] == []


@pytest.mark.asyncio
async def test_max_results_capping(mock_search_engine):
    """Test max results parameter validation."""
    mock_ddgs, _ = mock_search_engine
    tool = Search()
    mock_ddgs.return_value.text.return_value = []

    result = await tool.run(query="test", max_results=20)
    assert result.success
    # Should cap at 10
    mock_ddgs.return_value.text.assert_called_with("test", max_results=10)


@pytest.mark.asyncio
async def test_network_failure(mock_search_engine):
    """Test graceful handling of network failures."""
    mock_ddgs, _ = mock_search_engine
    tool = Search()
    mock_ddgs.return_value.text.side_effect = Exception("Network error")

    result = await tool.run(query="test")
    assert not result.success
    assert "DuckDuckGo search failed" in result.error


@pytest.mark.asyncio
async def test_rate_limiting(mock_search_engine):
    """Test rate limiting behavior."""
    mock_ddgs, mock_sleep = mock_search_engine
    tool = Search()
    mock_ddgs.return_value.text.return_value = []

    await tool.run(query="test")
    mock_sleep.assert_called_once_with(0.5)
