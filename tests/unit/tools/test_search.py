from unittest.mock import patch

import pytest

from cogency.tools import Search


@pytest.fixture
def mock_ddgs():
    with patch("ddgs.DDGS") as mock_lib:
        yield mock_lib


@pytest.mark.asyncio
async def test_finds_results(mock_ddgs):
    tool = Search()
    mock_ddgs.return_value.text.return_value = [
        {"title": "Result 1", "body": "Body 1", "href": "http://link1.com"},
        {"title": "Result 2", "body": "Body 2", "href": "http://link2.com"},
    ]

    result = await tool.execute(query="test query")

    assert not result.error
    assert "Found 2 results for 'test query'" in result.outcome
    assert "Result 1" in result.content
    assert "http://link2.com" in result.content
    mock_ddgs.return_value.text.assert_called_once_with("test query", max_results=5)


@pytest.mark.asyncio
async def test_empty_query():
    tool = Search()
    result = await tool.execute(query="")

    assert result.error
    assert "Search query cannot be empty" in result.outcome


@pytest.mark.asyncio
async def test_no_results(mock_ddgs):
    tool = Search()
    mock_ddgs.return_value.text.return_value = []

    result = await tool.execute(query="no results")

    assert not result.error
    assert "No results found" in result.content


@pytest.mark.asyncio
async def test_ddgs_import_error():
    with patch.dict("sys.modules", {"ddgs": None}):
        tool = Search()
        result = await tool.execute(query="test")

        assert result.error
        assert "DDGS metasearch not available" in result.outcome
