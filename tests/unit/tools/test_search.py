"""Search tool tests."""

from unittest.mock import patch

import pytest

from cogency.tools.search import Search


@pytest.mark.asyncio
async def test_success():
    tool = Search()
    mock_results = [{"title": "Test", "href": "https://example.com", "body": "Content"}]

    with patch("cogency.tools.search.DDGS") as mock_ddgs, patch("asyncio.sleep"):
        mock_ddgs.return_value.text.return_value = mock_results

        result = await tool.run(query="test query")
        assert result.success
        assert result.data["total_found"] == 1
        assert result.data["query"] == "test query"
        assert len(result.data["results"]) == 1
        assert result.data["results"][0]["title"] == "Test"


@pytest.mark.asyncio
async def test_no_results():
    tool = Search()

    with patch("cogency.tools.search.DDGS") as mock_ddgs, patch("asyncio.sleep"):
        mock_ddgs.return_value.text.return_value = []

        result = await tool.run(query="no results")
        assert result.success
        assert result.data["total_found"] == 0
        assert result.data["results"] == []


@pytest.mark.asyncio
async def test_max_results():
    tool = Search()

    with patch("cogency.tools.search.DDGS") as mock_ddgs, patch("asyncio.sleep"):
        mock_ddgs.return_value.text.return_value = []

        result = await tool.run(query="test", max_results=20)
        assert result.success
        # Should cap at 10
        mock_ddgs.return_value.text.assert_called_with("test", max_results=10)


@pytest.mark.asyncio
async def test_failure():
    tool = Search()

    with patch("cogency.tools.search.DDGS") as mock_ddgs, patch("asyncio.sleep"):
        mock_ddgs.return_value.text.side_effect = Exception("Network error")

        result = await tool.run(query="test")
        assert not result.success
        assert "DuckDuckGo search failed" in result.error


@pytest.mark.asyncio
async def test_rate_limit():
    tool = Search()

    with patch("cogency.tools.search.DDGS") as mock_ddgs, patch("asyncio.sleep") as mock_sleep:
        mock_ddgs.return_value.text.return_value = []

        await tool.run(query="test")
        mock_sleep.assert_called_once_with(1.0)
