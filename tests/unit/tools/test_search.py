"""Search tool tests."""

from unittest.mock import Mock, patch

import pytest

from cogency.tools.search import Search
from cogency.utils.results import ToolResult


@pytest.mark.asyncio
async def test_interface():
    search_tool = Search()

    assert search_tool.name == "search"
    assert search_tool.description
    assert hasattr(search_tool, "run")

    schema = search_tool.schema
    examples = search_tool.examples
    assert isinstance(schema, str) and len(schema) > 0
    assert isinstance(examples, list) and len(examples) > 0


@pytest.mark.asyncio
async def test_basic_search():
    search_tool = Search()

    mock_results = [{"title": "Test Result", "href": "https://example.com", "body": "Test content"}]

    with patch("cogency.tools.search.DDGS") as mock_ddgs, patch("time.sleep") as mock_sleep:
        mock_ddgs.return_value.text.return_value = mock_results

        result = await search_tool.run(query="test")
        assert result.success
        mock_sleep.assert_not_called()
