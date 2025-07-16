"""Unit tests for BaseMemory interface and SearchType enum."""
import pytest
from unittest.mock import Mock, AsyncMock
from cogency.memory.base import BaseMemory, MemoryArtifact, MemoryType, SearchType
from datetime import datetime, UTC
from uuid import uuid4


class TestSearchType:
    """Test SearchType enum functionality."""
    
    def test_search_type_values(self):
        """Test SearchType enum has expected values."""
        assert SearchType.AUTO.value == "auto"
        assert SearchType.SEMANTIC.value == "semantic"
        assert SearchType.TEXT.value == "text"
        assert SearchType.HYBRID.value == "hybrid"
    
    def test_search_type_from_string(self):
        """Test creating SearchType from string values."""
        assert SearchType("auto") == SearchType.AUTO
        assert SearchType("semantic") == SearchType.SEMANTIC
        assert SearchType("text") == SearchType.TEXT
        assert SearchType("hybrid") == SearchType.HYBRID


class MockMemory(BaseMemory):
    """Mock memory implementation for testing BaseMemory interface."""
    
    def __init__(self, embedding_provider=None):
        super().__init__(embedding_provider)
        self.artifacts = {}
        self.memorize_calls = []
        self.recall_calls = []
    
    async def memorize(self, content, memory_type=MemoryType.FACT, tags=None, metadata=None, timeout_seconds=10.0):
        """Mock memorize implementation."""
        self.memorize_calls.append({
            'content': content,
            'memory_type': memory_type,
            'tags': tags,
            'metadata': metadata,
            'timeout_seconds': timeout_seconds
        })
        
        artifact = MemoryArtifact(
            content=content,
            memory_type=memory_type,
            tags=tags or [],
            metadata=metadata or {}
        )
        self.artifacts[artifact.id] = artifact
        return artifact
    
    async def recall(self, query, search_type=SearchType.AUTO, limit=10, threshold=0.7, 
                    tags=None, memory_type=None, metadata_filter=None, since=None, **kwargs):
        """Mock recall implementation."""
        self.recall_calls.append({
            'query': query,
            'search_type': search_type,
            'limit': limit,
            'threshold': threshold,
            'tags': tags,
            'memory_type': memory_type,
            'metadata_filter': metadata_filter,
            'since': since,
            'kwargs': kwargs
        })
        
        # Simple mock logic - return artifacts containing query
        results = []
        for artifact in self.artifacts.values():
            if query.lower() in artifact.content.lower():
                artifact.relevance_score = 0.8
                results.append(artifact)
        
        return results[:limit]


class TestBaseMemory:
    """Test BaseMemory interface."""
    
    def test_base_memory_init_with_embedding_provider(self):
        """Test BaseMemory initialization with embedding provider."""
        mock_provider = Mock()
        memory = MockMemory(embedding_provider=mock_provider)
        
        assert memory.embedding_provider == mock_provider
    
    def test_base_memory_init_without_embedding_provider(self):
        """Test BaseMemory initialization without embedding provider."""
        memory = MockMemory()
        
        assert memory.embedding_provider is None
    
    @pytest.mark.asyncio
    async def test_memorize_interface(self):
        """Test memorize method interface."""
        memory = MockMemory()
        
        result = await memory.memorize(
            content="Test content",
            memory_type=MemoryType.CONTEXT,
            tags=["test", "example"],
            metadata={"key": "value"},
            timeout_seconds=5.0
        )
        
        assert isinstance(result, MemoryArtifact)
        assert result.content == "Test content"
        assert result.memory_type == MemoryType.CONTEXT
        assert result.tags == ["test", "example"]
        assert result.metadata == {"key": "value"}
        
        # Verify call was recorded
        assert len(memory.memorize_calls) == 1
        call = memory.memorize_calls[0]
        assert call['content'] == "Test content"
        assert call['memory_type'] == MemoryType.CONTEXT
        assert call['tags'] == ["test", "example"]
        assert call['metadata'] == {"key": "value"}
        assert call['timeout_seconds'] == 5.0
    
    @pytest.mark.asyncio
    async def test_memorize_with_defaults(self):
        """Test memorize method with default parameters."""
        memory = MockMemory()
        
        result = await memory.memorize("Test content")
        
        assert result.memory_type == MemoryType.FACT
        assert result.tags == []
        assert result.metadata == {}
        
        call = memory.memorize_calls[0]
        assert call['memory_type'] == MemoryType.FACT
        assert call['tags'] is None
        assert call['metadata'] is None
        assert call['timeout_seconds'] == 10.0
    
    @pytest.mark.asyncio
    async def test_recall_interface(self):
        """Test recall method interface."""
        memory = MockMemory()
        
        # Store some test data
        await memory.memorize("Test content about work")
        
        results = await memory.recall(
            query="work",
            search_type=SearchType.SEMANTIC,
            limit=5,
            threshold=0.8,
            tags=["work"],
            memory_type=MemoryType.FACT,
            metadata_filter={"category": "professional"},
            since="2024-01-01"
        )
        
        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0].content == "Test content about work"
        assert results[0].relevance_score == 0.8
        
        # Verify call was recorded
        assert len(memory.recall_calls) == 1
        call = memory.recall_calls[0]
        assert call['query'] == "work"
        assert call['search_type'] == SearchType.SEMANTIC
        assert call['limit'] == 5
        assert call['threshold'] == 0.8
        assert call['tags'] == ["work"]
        assert call['memory_type'] == MemoryType.FACT
        assert call['metadata_filter'] == {"category": "professional"}
        assert call['since'] == "2024-01-01"
    
    @pytest.mark.asyncio
    async def test_recall_with_defaults(self):
        """Test recall method with default parameters."""
        memory = MockMemory()
        
        await memory.memorize("Test content")
        results = await memory.recall("test")
        
        assert len(results) == 1
        
        call = memory.recall_calls[0]
        assert call['search_type'] == SearchType.AUTO
        assert call['limit'] == 10
        assert call['threshold'] == 0.7
        assert call['tags'] is None
        assert call['memory_type'] is None
        assert call['metadata_filter'] is None
        assert call['since'] is None
    
    @pytest.mark.asyncio
    async def test_forget_not_implemented(self):
        """Test forget method raises NotImplementedError by default."""
        memory = MockMemory()
        
        with pytest.raises(NotImplementedError, match="forget\\(\\) not implemented"):
            await memory.forget(uuid4())
    
    @pytest.mark.asyncio
    async def test_clear_not_implemented(self):
        """Test clear method raises NotImplementedError by default."""
        memory = MockMemory()
        
        with pytest.raises(NotImplementedError, match="clear\\(\\) not implemented"):
            await memory.clear()
    
    @pytest.mark.asyncio
    async def test_inspect_interface(self):
        """Test inspect method interface."""
        memory = MockMemory()
        
        # Store some test data
        await memory.memorize("First test content", tags=["test"])
        await memory.memorize("Second test content", tags=["example"])
        
        stats = await memory.inspect()
        
        assert isinstance(stats, dict)
        assert "count" in stats
        assert "recent" in stats
        assert stats["count"] == 2
        assert len(stats["recent"]) == 2
        
        # Check recent items format
        recent_item = stats["recent"][0]
        assert "content" in recent_item
        assert "tags" in recent_item
        assert "created" in recent_item
        assert len(recent_item["content"]) <= 53  # 50 chars + "..."