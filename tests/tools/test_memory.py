"""NO BULLSHIT memory tool tests - only test real bugs that break shit."""
import pytest
from unittest.mock import Mock, AsyncMock
from cogency.tools.memory import MemorizeTool, RecallTool
from cogency.memory.base import BaseMemory
from cogency.memory import MemoryArtifact
from datetime import datetime


class TestMemorizeTool:
    """Test MemorizeTool - focus on real bugs."""
    
    @pytest.fixture
    def mock_memory(self):
        memory = Mock(spec=BaseMemory)
        memory.memorize = AsyncMock()
        return memory
    
    @pytest.fixture
    def memorize_tool(self, mock_memory):
        return MemorizeTool(mock_memory)
    
    @pytest.mark.asyncio
    async def test_memorize_with_content_and_tags(self, memorize_tool, mock_memory):
        """Test memorize with content and tags - REAL BUG."""
        # Mock artifact
        artifact = MemoryArtifact(
            id="test-id",
            content="test content",
            tags=["tag1", "tag2"],
            metadata={},
            created_at=datetime.now()
        )
        mock_memory.memorize.return_value = artifact
        
        # This should NOT crash with parsing errors
        result = await memorize_tool.run(
            content="test content",
            tags=["tag1", "tag2"]
        )
        
        assert result["success"] is True
        assert result["artifact_id"] == "test-id"
        assert result["tags"] == ["tag1", "tag2"]
        mock_memory.memorize.assert_called_once_with(
            "test content", 
            tags=["tag1", "tag2"], 
            metadata={}
        )
    
    @pytest.mark.asyncio
    async def test_memorize_missing_content(self, memorize_tool):
        """Test memorize without content - REAL BUG."""
        result = await memorize_tool.run()
        
        assert "error" in result
        assert "content parameter is required" in result["error"]
    
    @pytest.mark.asyncio
    async def test_memorize_handles_exceptions(self, memorize_tool, mock_memory):
        """Test memorize handles memory exceptions - REAL BUG."""
        mock_memory.memorize.side_effect = Exception("Memory storage failed")
        
        result = await memorize_tool.run(content="test")
        
        assert "error" in result
        assert "Failed to memorize content" in result["error"]


class TestRecallTool:
    """Test RecallTool - focus on real bugs."""
    
    @pytest.fixture
    def mock_memory(self):
        memory = Mock(spec=BaseMemory)
        memory.recall = AsyncMock()
        return memory
    
    @pytest.fixture
    def recall_tool(self, mock_memory):
        return RecallTool(mock_memory)
    
    @pytest.mark.asyncio
    async def test_recall_with_query(self, recall_tool, mock_memory):
        """Test recall with query - REAL BUG."""
        # Mock artifacts
        artifact = MemoryArtifact(
            id="test-id",
            content="test content",
            tags=["tag1"],
            metadata={},
            created_at=datetime.now()
        )
        mock_memory.recall.return_value = [artifact]
        
        result = await recall_tool.run(query="test query")
        
        assert result["success"] is True
        assert result["results_count"] == 1
        assert result["results"][0]["id"] == "test-id"
        assert result["results"][0]["content"] == "test content"
        mock_memory.recall.assert_called_once_with(
            "test query", 
            limit=None, 
            tags=None
        )
    
    @pytest.mark.asyncio
    async def test_recall_missing_query(self, recall_tool):
        """Test recall without query - REAL BUG."""
        result = await recall_tool.run()
        
        assert "error" in result
        assert "query parameter is required" in result["error"]
    
    @pytest.mark.asyncio
    async def test_recall_handles_exceptions(self, recall_tool, mock_memory):
        """Test recall handles memory exceptions - REAL BUG."""
        mock_memory.recall.side_effect = Exception("Memory recall failed")
        
        result = await recall_tool.run(query="test")
        
        assert "error" in result
        assert "Failed to recall content" in result["error"]