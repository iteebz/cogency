"""Test tag-based search functionality."""

import pytest
from unittest.mock import AsyncMock

from cogency.memory.backends.filesystem import FilesystemBackend
from cogency.memory.core import SearchType, MemoryType
# Removed hardcoded tag extraction - now using LLM dynamic generation


@pytest.fixture
def fs_memory_tags(mock_embedding_provider, tmp_path):
    return FilesystemBackend(
        memory_dir=str(tmp_path / "tag_memory"),
        embedding_provider=mock_embedding_provider
    )


@pytest.mark.asyncio
class TestTagSearch:
    
    async def test_llm_based_tagging_integration(self, fs_memory_tags):
        """Test that LLM-based tag generation works in practice."""
        # This test verifies the integration works, actual tag generation 
        # is tested through Pre-ReAct flow with real LLM calls
        content = "Authentication bug in login system"
        
        # Store memory with manually provided tags (simulating LLM output)
        await fs_memory_tags.memorize(
            content=content,
            memory_type=MemoryType.FACT,
            tags=["security", "problem", "web"]  # LLM-generated tags
        )
        
        # Verify tags work for search
        results = await fs_memory_tags.recall_by_tags(["security"])
        assert len(results) == 1
        assert results[0].content == content
    
    async def test_tag_only_search(self, fs_memory_tags):
        """Test pure tag-based search."""
        # Store memories with different tags
        await fs_memory_tags.memorize(
            content="Authentication bug in login flow",
            memory_type=MemoryType.FACT,
            tags=["problem", "security", "extracted"]
        )
        await fs_memory_tags.memorize(
            content="Performance optimization for database queries",
            memory_type=MemoryType.FACT,
            tags=["solution", "performance", "data", "extracted"]
        )
        await fs_memory_tags.memorize(
            content="User reported slow response times",
            memory_type=MemoryType.EPISODIC,
            tags=["problem", "performance", "extracted"]
        )
        
        # Search by single tag
        results = await fs_memory_tags.recall_by_tags(["security"])
        assert len(results) == 1
        assert "Authentication bug" in results[0].content
        
        # Search by multiple tags (AND logic)
        results = await fs_memory_tags.recall_by_tags(["problem", "performance"])
        assert len(results) == 1
        assert "slow response times" in results[0].content
        
        # Search with TAGS search type directly
        results = await fs_memory_tags.recall(
            query="ignored for tag search",
            search_type=SearchType.TAGS,
            tags=["solution"]
        )
        assert len(results) == 1
        assert "optimization" in results[0].content
    
    async def test_smart_recall(self, fs_memory_tags):
        """Test smart recall that combines query and tags."""
        # Store test data
        await fs_memory_tags.memorize(
            content="Database connection pool configuration for performance",
            tags=["solution", "data", "performance"]
        )
        await fs_memory_tags.memorize(
            content="API rate limiting causes performance degradation", 
            tags=["problem", "performance", "web"]
        )
        
        # Tag-only search (no query)
        results = await fs_memory_tags.recall_smart("", tags=["solution"])
        assert len(results) == 1
        assert "connection pool" in results[0].content
        
        # Hybrid search with tags
        results = await fs_memory_tags.recall_smart(
            "performance issues",
            tags=["problem"]
        )
        assert len(results) == 1
        assert "rate limiting" in results[0].content
        
        # Regular search (no tags)
        results = await fs_memory_tags.recall_smart("database")
        assert len(results) >= 1
    
    async def test_tag_statistics(self, fs_memory_tags):
        """Test tag statistics and inspection."""
        # Store memories with various tags
        test_data = [
            ("First memory", ["ai", "programming", "extracted"]),
            ("Second memory", ["ai", "data", "extracted"]), 
            ("Third memory", ["programming", "web", "extracted"]),
            ("Fourth memory", ["priority", "ai", "extracted"])
        ]
        
        for content, tags in test_data:
            await fs_memory_tags.memorize(content, tags=tags)
        
        # Get all unique tags
        all_tags = await fs_memory_tags.get_all_tags()
        expected_tags = {'ai', 'data', 'extracted', 'priority', 'programming', 'web'}
        assert set(all_tags) == expected_tags
        
        # Inspect memory stats
        stats = await fs_memory_tags.inspect()
        assert stats["count"] == 4
        assert stats["unique_tags"] == 6
        
        # Check top tags (should be sorted by frequency)
        top_tags = dict(stats["top_tags"])
        assert top_tags["ai"] == 3  # Most frequent
        assert top_tags["extracted"] == 4  # All memories have this
    
    async def test_priority_tag_boosting(self, fs_memory_tags):
        """Test that priority tags get relevance boost."""
        # Store regular memory
        await fs_memory_tags.memorize(
            content="Regular task to complete",
            tags=["solution", "extracted"]
        )
        
        # Store priority memory
        await fs_memory_tags.memorize(
            content="Critical security fix needed",
            tags=["priority", "security", "extracted"]
        )
        
        # Tag search should rank priority items higher
        results = await fs_memory_tags.recall_by_tags(["extracted"], limit=10)
        assert len(results) == 2
        
        # Priority memory should score higher
        priority_result = next(r for r in results if "Critical" in r.content)
        regular_result = next(r for r in results if "Regular" in r.content)
        
        assert priority_result.relevance_score > regular_result.relevance_score
    
    async def test_tags_search_with_filters(self, fs_memory_tags):
        """Test tag search combined with other filters."""
        # Store memories with different types and tags
        await fs_memory_tags.memorize(
            content="Fact about AI algorithms",
            memory_type=MemoryType.FACT,
            tags=["ai", "learning"]
        )
        await fs_memory_tags.memorize(
            content="Experience with debugging AI models",
            memory_type=MemoryType.EXPERIENCE,
            tags=["ai", "problem"]
        )
        
        # Search by tags + memory type
        results = await fs_memory_tags.recall(
            query="",
            search_type=SearchType.TAGS,
            tags=["ai"],
            memory_type=MemoryType.FACT
        )
        
        assert len(results) == 1
        assert "algorithms" in results[0].content
        assert results[0].memory_type == MemoryType.FACT