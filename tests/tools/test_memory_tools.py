"""Memory tools unit tests."""
import pytest
from unittest.mock import Mock
from cogency.tools.memory import MemorizeTool, RecallTool
from cogency.memory.base import BaseMemory, MemoryArtifact
from datetime import datetime
import uuid


class MockMemory(BaseMemory):
    """Mock memory for testing."""
    
    def __init__(self):
        self.artifacts = {}
    
    async def memorize(self, content: str, tags: list = None, metadata: dict = None) -> MemoryArtifact:
        """Store content and return artifact."""
        artifact_id = str(uuid.uuid4())
        artifact = MemoryArtifact(
            id=artifact_id,
            content=content,
            tags=tags or [],
            metadata=metadata or {},
            created_at=datetime.now()
        )
        self.artifacts[artifact_id] = artifact
        return artifact
    
    async def recall(self, query: str, limit: int = None, tags: list = None) -> list[MemoryArtifact]:
        """Retrieve matching artifacts."""
        results = []
        for artifact in self.artifacts.values():
            if query.lower() in artifact.content.lower():
                if not tags or any(tag in artifact.tags for tag in tags):
                    results.append(artifact)
        return results[:limit] if limit else results
    
    def should_store(self, content: str) -> tuple[bool, str]:
        """Mock smart categorization."""
        if "personal" in content.lower():
            return True, "personal"
        elif "work" in content.lower():
            return True, "work"
        return False, ""


class TestMemorizeTools:
    """Test memory tools functionality."""
    
    @pytest.mark.asyncio
    async def test_memorize_tool_basic(self):
        """Test basic memorize tool functionality."""
        memory = MockMemory()
        tool = MemorizeTool(memory)
        
        result = await tool.run(content="Test content", tags=["test"])
        
        assert result["success"] == True
        assert "artifact_id" in result
        assert result["content_preview"] == "Test content"
        assert result["tags"] == ["test"]
    
    @pytest.mark.asyncio
    async def test_memorize_tool_auto_tagging(self):
        """Test memorize tool with auto-tagging."""
        memory = MockMemory()
        tool = MemorizeTool(memory)
        
        result = await tool.run(content="I work as a developer")
        
        assert result["success"] == True
        assert result["tags"] == ["work"]
    
    @pytest.mark.asyncio
    async def test_memorize_tool_no_content(self):
        """Test memorize tool with missing content."""
        memory = MockMemory()
        tool = MemorizeTool(memory)
        
        result = await tool.run()
        
        assert "error" in result
        assert "content parameter is required" in result["error"]
    
    @pytest.mark.asyncio
    async def test_recall_tool_basic(self):
        """Test basic recall tool functionality."""
        memory = MockMemory()
        recall_tool = RecallTool(memory)
        
        # First store some content
        await memory.memorize("Test content about work", tags=["work"])
        
        result = await recall_tool.run(query="work")
        
        assert result["success"] == True
        assert result["results_count"] == 1
        assert "work" in result["results"][0]["content"]
    
    @pytest.mark.asyncio
    async def test_recall_tool_no_query(self):
        """Test recall tool with missing query."""
        memory = MockMemory()
        tool = RecallTool(memory)
        
        result = await tool.run()
        
        assert "error" in result
        assert "query parameter is required" in result["error"]
    
    @pytest.mark.asyncio
    async def test_recall_tool_with_limit(self):
        """Test recall tool with limit parameter."""
        memory = MockMemory()
        recall_tool = RecallTool(memory)
        
        # Store multiple items
        await memory.memorize("First test item", tags=["test"])
        await memory.memorize("Second test item", tags=["test"])
        
        result = await recall_tool.run(query="test", limit=1)
        
        assert result["success"] == True
        assert result["results_count"] == 1