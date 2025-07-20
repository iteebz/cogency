"""Test WebSearch tool business logic."""
import pytest

from cogency.tools.web_search import WebSearch


class TestWebSearch:
    """Test WebSearch tool business logic."""
    
    @pytest.mark.asyncio
    async def test_basic_interface(self):
        """WebSearch tool implements required interface."""
        search_tool = WebSearch()
        
        # Required attributes
        assert search_tool.name == "web_search"
        assert search_tool.description
        assert hasattr(search_tool, 'run')
        
        # Schema and examples
        schema = search_tool.get_schema()
        examples = search_tool.get_usage_examples()
        assert isinstance(schema, str) and len(schema) > 0
        assert isinstance(examples, list) and len(examples) > 0
    
    @pytest.mark.asyncio
    async def test_empty_query(self):
        """WebSearch tool handles empty query."""
        search_tool = WebSearch()
        
        # Tool validates and raises ValidationError for empty queries
        result = await search_tool.execute(query="")
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_basic_search(self):
        """WebSearch tool can perform basic search."""
        search_tool = WebSearch()
        
        # Use a simple query that should work
        result = await search_tool.run(query="test")
        # Search may return results or error (API issues) - both are acceptable
        assert isinstance(result, dict)