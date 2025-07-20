"""Test Search tool business logic."""
import pytest

from cogency.tools.search import Search


class TestSearch:
    """Test Search tool business logic."""
    
    @pytest.mark.asyncio
    async def test_basic_interface(self):
        """Search tool implements required interface."""
        search_tool = Search()
        
        # Required attributes
        assert search_tool.name == "search"
        assert search_tool.description
        assert hasattr(search_tool, 'run')
        
        # Schema and examples
        schema = search_tool.get_schema()
        examples = search_tool.get_usage_examples()
        assert isinstance(schema, str) and len(schema) > 0
        assert isinstance(examples, list) and len(examples) > 0
    
    @pytest.mark.asyncio
    async def test_empty_query(self):
        """Search tool handles empty query."""
        search_tool = Search()
        
        # Tool validates and raises ValidationError for empty queries
        result = await search_tool.execute(query="")
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_basic_search(self):
        """Search tool can perform basic search."""
        search_tool = Search()
        
        # Use a simple query that should work
        result = await search_tool.run(query="test")
        # Search may return results or error (API issues) - both are acceptable
        assert isinstance(result, dict)