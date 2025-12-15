from unittest.mock import patch

import pytest

from cogency.tools import Search


@pytest.fixture
def mock_ddgs():
    with patch("ddgs.DDGS") as mock_lib:
        yield mock_lib


@pytest.mark.asyncio
async def test_finds_results(mock_ddgs):
    mock_ddgs.return_value.text.return_value = [
        {"title": "Result 1", "body": "Body 1", "href": "http://link1.com"},
        {"title": "Result 2", "body": "Body 2", "href": "http://link2.com"},
    ]

    result = await Search.execute(query="test query")

    assert not result.error
    assert "Found 2 results for 'test query'" in result.outcome
    assert result.content is not None
    assert "Result 1" in result.content
    assert "http://link2.com" in result.content
    mock_ddgs.return_value.text.assert_called_once_with("test query", max_results=5)


@pytest.mark.asyncio
async def test_empty_query():
    result = await Search.execute(query="")

    assert result.error
    assert "Search query cannot be empty" in result.outcome


@pytest.mark.asyncio
async def test_no_results(mock_ddgs):
    mock_ddgs.return_value.text.return_value = []

    result = await Search.execute(query="no results")

    assert not result.error
    assert result.content is not None
    assert "No results found" in result.content


@pytest.mark.asyncio
async def test_ddgs_import_error():
    with patch.dict("sys.modules", {"ddgs": None}):
        result = await Search.execute(query="test")

        assert result.error
        assert "DDGS metasearch not available" in result.outcome
