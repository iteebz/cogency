"""Edge case tests for hybrid search functionality."""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime, timezone

from cogency.memory.filesystem import FSMemory
from cogency.memory.base import SearchType, MemoryType, MemoryArtifact


@pytest.fixture
def fs_memory_hybrid(mock_embedding_provider, tmp_path):
    memory = FSMemory(
        memory_dir=str(tmp_path / "test_memory"),
        embedding_provider=mock_embedding_provider
    )
    return memory


@pytest.mark.asyncio
class TestHybridSearchEdgeCases:
    
    async def test_hybrid_empty_query(self, fs_memory_hybrid):
        """Test hybrid search with empty query string."""
        results = await fs_memory_hybrid.recall(
            query="",
            search_type=SearchType.HYBRID
        )
        assert results == []
    
    async def test_hybrid_no_memories(self, fs_memory_hybrid):
        """Test hybrid search when no memories exist."""
        results = await fs_memory_hybrid.recall(
            query="test query",
            search_type=SearchType.HYBRID
        )
        assert results == []
    
    async def test_hybrid_semantic_only_results(self, fs_memory_hybrid):
        """Test hybrid when only semantic search returns results."""
        # Store memory with embedding
        await fs_memory_hybrid.memorize(
            content="machine learning algorithms",
            memory_type=MemoryType.FACT,
            tags=["ai"]
        )
        
        # Query that matches semantically but not textually
        results = await fs_memory_hybrid.recall(
            query="artificial intelligence",
            search_type=SearchType.HYBRID,
            limit=5
        )
        
        assert len(results) == 1
        assert "machine learning" in results[0].content
    
    async def test_hybrid_text_only_results(self, fs_memory_hybrid):
        """Test hybrid when only text search returns results."""
        # Store memory without embedding (simulate embedding failure)
        original_embed = fs_memory_hybrid.embedding_provider.embed
        fs_memory_hybrid.embedding_provider.embed = AsyncMock(side_effect=Exception("No embedding"))
        
        await fs_memory_hybrid.memorize(
            content="exact keyword match test",
            memory_type=MemoryType.FACT
        )
        
        # Restore embedding for query
        fs_memory_hybrid.embedding_provider.embed = original_embed
        
        results = await fs_memory_hybrid.recall(
            query="exact keyword",
            search_type=SearchType.HYBRID,
            limit=5
        )
        
        assert len(results) == 1
        assert "exact keyword match" in results[0].content
    
    async def test_hybrid_overlapping_results(self, fs_memory_hybrid):
        """Test hybrid when both searches return the same result."""
        await fs_memory_hybrid.memorize(
            content="python programming language",
            memory_type=MemoryType.FACT,
            tags=["coding"]
        )
        
        results = await fs_memory_hybrid.recall(
            query="python programming",
            search_type=SearchType.HYBRID,
            limit=5
        )
        
        # Should not duplicate the same memory
        assert len(results) == 1
        assert "python programming" in results[0].content
    
    async def test_hybrid_different_thresholds(self, fs_memory_hybrid):
        """Test hybrid search respects different similarity thresholds."""
        # Store memories with varying similarity
        await fs_memory_hybrid.memorize(
            content="high similarity content match",
            memory_type=MemoryType.FACT
        )
        await fs_memory_hybrid.memorize(
            content="medium relevance topic",
            memory_type=MemoryType.FACT
        )
        
        # High threshold - fewer results
        high_threshold_results = await fs_memory_hybrid.recall(
            query="content",
            search_type=SearchType.HYBRID,
            threshold=0.9
        )
        
        # Low threshold - more results
        low_threshold_results = await fs_memory_hybrid.recall(
            query="content",
            search_type=SearchType.HYBRID,
            threshold=0.3
        )
        
        assert len(low_threshold_results) >= len(high_threshold_results)
    
    async def test_hybrid_limit_enforcement(self, fs_memory_hybrid):
        """Test hybrid search respects result limits."""
        # Store multiple memories
        for i in range(10):
            await fs_memory_hybrid.memorize(
                content=f"test content number {i}",
                memory_type=MemoryType.FACT
            )
        
        results = await fs_memory_hybrid.recall(
            query="test content",
            search_type=SearchType.HYBRID,
            limit=3
        )
        
        assert len(results) <= 3
    
    async def test_hybrid_score_combination(self, fs_memory_hybrid):
        """Test that hybrid scores are properly combined."""
        # Store memory that should score well in both text and semantic
        await fs_memory_hybrid.memorize(
            content="machine learning neural networks deep learning",
            memory_type=MemoryType.FACT
        )
        
        # Store memory that should score well only in text
        original_embed = fs_memory_hybrid.embedding_provider.embed
        fs_memory_hybrid.embedding_provider.embed = AsyncMock(side_effect=Exception("No embedding"))
        
        await fs_memory_hybrid.memorize(
            content="machine learning exact phrase match",
            memory_type=MemoryType.FACT
        )
        
        # Restore embedding
        fs_memory_hybrid.embedding_provider.embed = original_embed
        
        results = await fs_memory_hybrid.recall(
            query="machine learning",
            search_type=SearchType.HYBRID,
            limit=5
        )
        
        assert len(results) == 2
        # Results should be ordered by combined score
        for result in results:
            assert hasattr(result, 'content')
            assert "machine learning" in result.content
    
    async def test_hybrid_with_filters(self, fs_memory_hybrid):
        """Test hybrid search with various filters applied."""
        # Store memories with different tags and types
        await fs_memory_hybrid.memorize(
            content="important machine learning fact",
            memory_type=MemoryType.FACT,
            tags=["important", "ai"]
        )
        await fs_memory_hybrid.memorize(
            content="casual machine learning note",
            memory_type=MemoryType.EPISODIC,
            tags=["casual"]
        )
        
        # Filter by tag
        tag_results = await fs_memory_hybrid.recall(
            query="machine learning",
            search_type=SearchType.HYBRID,
            tags=["important"]
        )
        
        assert len(tag_results) == 1
        assert "important" in tag_results[0].content
        
        # Filter by memory type
        type_results = await fs_memory_hybrid.recall(
            query="machine learning",
            search_type=SearchType.HYBRID,
            memory_type=MemoryType.EPISODIC
        )
        
        assert len(type_results) == 1
        assert "casual" in type_results[0].content
    
    async def test_hybrid_embedding_provider_failure(self, fs_memory_hybrid):
        """Test hybrid gracefully handles embedding provider failures."""
        # Store memory normally
        await fs_memory_hybrid.memorize(
            content="test content for hybrid search",
            memory_type=MemoryType.FACT
        )
        
        # Break embedding provider during recall
        fs_memory_hybrid.embedding_provider.embed = AsyncMock(side_effect=Exception("Embedding service down"))
        
        # Should still work with text search only
        results = await fs_memory_hybrid.recall(
            query="test content",
            search_type=SearchType.HYBRID
        )
        
        assert len(results) == 1
        assert "test content" in results[0].content
    
    async def test_hybrid_deduplication(self, fs_memory_hybrid):
        """Test that hybrid search properly deduplicates results."""
        # Create memory that will match both text and semantic searches
        await fs_memory_hybrid.memorize(
            content="python programming language tutorial",
            memory_type=MemoryType.FACT,
            tags=["programming"]
        )
        
        results = await fs_memory_hybrid.recall(
            query="python tutorial",  # Should match both ways
            search_type=SearchType.HYBRID,
            limit=10
        )
        
        # Should only return one result, not duplicated
        assert len(results) == 1
        
        # Verify it's the correct result
        assert "python programming language tutorial" == results[0].content