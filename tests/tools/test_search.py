"""Test Search tool business logic."""

from unittest.mock import Mock, patch

import pytest

from cogency.tools.search import Search
from cogency.utils.results import ToolResult


class TestSearch:
    """Test Search tool business logic."""

    @pytest.mark.asyncio
    async def test_interface(self):
        """Search tool implements required interface."""
        search_tool = Search()

        # Required attributes
        assert search_tool.name == "search"
        assert search_tool.description
        assert hasattr(search_tool, "run")

        # Schema and examples
        schema = search_tool.schema
        examples = search_tool.examples
        assert isinstance(schema, str) and len(schema) > 0
        assert isinstance(examples, list) and len(examples) > 0

    @pytest.mark.asyncio
    async def test_empty_query(self):
        """Search tool handles empty query."""
        search_tool = Search()

        # Tool validates and raises ValidationError for empty queries
        result = await search_tool.execute(query="")
        assert not result.success

    @pytest.mark.asyncio
    async def test_basic_search(self):
        """Search tool can perform basic search."""
        search_tool = Search()

        # Mock DDGS to return fake search results
        mock_results = [
            {"title": "Test Result", "href": "https://example.com", "body": "Test content"}
        ]

        with patch("cogency.tools.search.DDGS") as mock_ddgs, patch("time.sleep") as mock_sleep:
            mock_ddgs.return_value.text.return_value = mock_results

            result = await search_tool.run(query="test")
            assert result.success
            mock_sleep.assert_not_called()  # Should not sleep for rate limiting
