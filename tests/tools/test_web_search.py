"""Web search tool unit tests."""
import pytest
from unittest.mock import AsyncMock, patch, Mock
from ddgs import DDGS
from cogency.utils.errors import ValidationError, ToolError
from cogency.tools.web_search import WebSearchTool


class TestWebSearchTool:
    """Test web search tool functionality."""
    
    @pytest.mark.asyncio
    async def test_search_execution(self):
        """Test search execution with mock DDGS response."""
        mock_ddgs = Mock(spec=DDGS)
        mock_ddgs.text.return_value = [
            {"title": "Test Result 1", "body": "Test snippet 1", "href": "http://example.com/1"},
            {"title": "Test Result 2", "body": "Test snippet 2", "href": "http://example.com/2"},
        ]
        
        with patch('cogency.tools.web_search.DDGS', return_value=mock_ddgs):
            search = WebSearchTool()
            result = await search.run(query="test query", max_results=2)
            
            assert "message" in result
            assert "query" in result
            assert "total_found" in result
            assert result["total_found"] == 2
            assert "top_result" in result
            assert result["top_result"]["title"] == "Test Result 1"
            mock_ddgs.text.assert_called_once_with("test query", max_results=2)

    @pytest.mark.asyncio
    async def test_search_execution_no_results(self):
        """Test search execution when no results are found."""
        mock_ddgs = Mock(spec=DDGS)
        mock_ddgs.text.return_value = []
        
        with patch('cogency.tools.web_search.DDGS', return_value=mock_ddgs):
            search = WebSearchTool()
            result = await search.run(query="nonexistent query")
            
            assert "message" in result
            assert "No results found" in result["message"]
            assert result["total_found"] == 0
            assert "top_result" not in result or result["top_result"] is None

    @pytest.mark.asyncio
    async def test_search_execution_max_results_cap(self):
        """Test that max_results is capped at 10."""
        mock_ddgs = Mock(spec=DDGS)
        mock_ddgs.text.return_value = [] # Don't care about content for this test
        
        with patch('cogency.tools.web_search.DDGS', return_value=mock_ddgs):
            search = WebSearchTool()
            await search.run(query="test query", max_results=15)
            
            mock_ddgs.text.assert_called_once_with("test query", max_results=10)

    @pytest.mark.asyncio
    async def test_search_execution_invalid_max_results(self):
        """Test invalid max_results handling."""
        search = WebSearchTool()
        result = await search.run(query="test query", max_results=0)
        assert "error" in result
        assert "max_results must be a positive integer" in result["error"]
        
        result = await search.run(query="test query", max_results=-5)
        assert "error" in result
        assert "max_results must be a positive integer" in result["error"]
        
        result = await search.run(query="test query", max_results="abc")
        assert "error" in result
        assert "max_results must be a positive integer" in result["error"]

    @pytest.mark.asyncio
    async def test_search_execution_tool_error(self):
        """Test tool error handling."""
        mock_ddgs = Mock(spec=DDGS)
        mock_ddgs.text.side_effect = Exception("DDGS error")
        
        with patch('cogency.tools.web_search.DDGS', return_value=mock_ddgs):
            search = WebSearchTool()
            result = await search.run(query="test query")
            
            assert "error" in result
            assert "DuckDuckGo search failed" in result["error"]