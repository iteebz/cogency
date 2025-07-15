"""Web search tool unit tests."""
import pytest
from unittest.mock import AsyncMock, patch
from cogency.tools.web_search import WebSearchTool


class TestWebSearchTool:
    """Test web search tool functionality."""
    
    @pytest.mark.asyncio
    async def test_search_execution(self):
        """Test search execution with mock response."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock the response
            mock_response = AsyncMock()
            mock_response.text = AsyncMock(return_value='{"results": [{"title": "Test Result", "snippet": "Test snippet"}]}')
            mock_get.return_value.__aenter__.return_value = mock_response
            
            search = WebSearchTool()
            result = await search.run("search", "test query")
            
            assert "results" in result
            assert isinstance(result["results"], list)
    
    @pytest.mark.asyncio
    async def test_invalid_action(self):
        """Test invalid action handling."""
        search = WebSearchTool()
        with pytest.raises(ValueError):
            await search.run("invalid_action", "query")