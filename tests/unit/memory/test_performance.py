"""Performance tests for memory backends with large embedding collections."""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock

from cogency.memory.backends.filesystem import FilesystemBackend
from cogency.memory.core import SearchType, MemoryType


@pytest.fixture
def perf_embedding_provider():
    """Mock embedding provider that simulates realistic embedding generation time."""
    provider = AsyncMock()
    
    async def mock_embed(text):
        # Simulate small delay for embedding generation
        await asyncio.sleep(0.001)
        # Return predictable but different embeddings based on text hash
        base = hash(text) % 1000 / 1000.0
        return [base + i * 0.1 for i in range(384)]  # 384-dim embedding
    
    provider.embed = mock_embed
    return provider


@pytest.fixture
def perf_memory(perf_embedding_provider, tmp_path):
    """Memory instance optimized for performance testing."""
    return FilesystemBackend(
        memory_dir=str(tmp_path / "perf_memory"),
        embedding_provider=perf_embedding_provider
    )


@pytest.mark.asyncio
class TestMemoryPerformance:
    
    async def test_batch_memorize_performance(self, perf_memory):
        """Test performance of batch memorization."""
        start_time = time.time()
        
        # Memorize 100 items
        tasks = []
        for i in range(100):
            task = perf_memory.memorize(
                content=f"Performance test content item {i}",
                memory_type=MemoryType.FACT,
                tags=[f"batch-{i//10}", "performance"]
            )
            tasks.append(task)
        
        # Execute all memorizations concurrently
        await asyncio.gather(*tasks)
        
        elapsed = time.time() - start_time
        
        # Should complete 100 memorizations in reasonable time
        assert elapsed < 10.0, f"Batch memorize took {elapsed:.2f}s, expected < 10s"
        
        # Verify all memories were stored
        all_memories = await perf_memory.recall(
            query="performance test",
            search_type=SearchType.TEXT,
            limit=200
        )
        assert len(all_memories) == 100
    
    async def test_semantic_search_performance(self, perf_memory):
        """Test semantic search performance with large collection."""
        # Pre-populate with many memories
        for i in range(200):
            await perf_memory.memorize(
                content=f"Document {i}: artificial intelligence and machine learning topic {i}",
                memory_type=MemoryType.FACT,
                tags=[f"topic-{i//20}"]
            )
        
        # Test search performance
        start_time = time.time()
        
        results = await perf_memory.recall(
            query="artificial intelligence machine learning",
            search_type=SearchType.SEMANTIC,
            limit=20,
            threshold=0.5
        )
        
        elapsed = time.time() - start_time
        
        # Search should be fast even with 200 items
        assert elapsed < 2.0, f"Semantic search took {elapsed:.2f}s, expected < 2s"
        assert len(results) > 0, "Should return some results"
        assert len(results) <= 20, "Should respect limit"
    
    async def test_hybrid_search_performance(self, perf_memory):
        """Test hybrid search performance scaling."""
        # Pre-populate with diverse content
        contents = [
            "machine learning algorithms neural networks",
            "data science analytics visualization",
            "artificial intelligence deep learning",
            "python programming software development",
            "database optimization query performance"
        ]
        
        # Create 50 variations of each content type
        for i in range(50):
            for j, base_content in enumerate(contents):
                await perf_memory.memorize(
                    content=f"{base_content} variation {i}",
                    memory_type=MemoryType.FACT,
                    tags=[f"category-{j}", f"variation-{i}"]
                )
        
        # Test hybrid search performance
        start_time = time.time()
        
        results = await perf_memory.recall(
            query="machine learning neural networks",
            search_type=SearchType.HYBRID,
            limit=15,
            threshold=0.3
        )
        
        elapsed = time.time() - start_time
        
        # Hybrid search should complete reasonably fast with 250 items
        assert elapsed < 3.0, f"Hybrid search took {elapsed:.2f}s, expected < 3s"
        assert len(results) > 0, "Should return some results"
        assert len(results) <= 15, "Should respect limit"
    
    async def test_concurrent_operations_performance(self, perf_memory):
        """Test performance under concurrent read/write operations."""
        # Pre-populate some data
        for i in range(20):
            await perf_memory.memorize(
                content=f"Base content item {i}",
                memory_type=MemoryType.FACT
            )
        
        start_time = time.time()
        
        # Create mixed workload: reads and writes happening concurrently
        tasks = []
        
        # Add 30 concurrent writes
        for i in range(30):
            task = perf_memory.memorize(
                content=f"Concurrent write {i}",
                memory_type=MemoryType.EPISODIC,
                tags=["concurrent"]
            )
            tasks.append(task)
        
        # Add 20 concurrent reads
        for i in range(20):
            task = perf_memory.recall(
                query=f"content {i % 10}",
                search_type=SearchType.SEMANTIC,
                limit=5
            )
            tasks.append(task)
        
        # Execute all operations concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        elapsed = time.time() - start_time
        
        # Should handle 50 concurrent operations efficiently
        assert elapsed < 8.0, f"Concurrent ops took {elapsed:.2f}s, expected < 8s"
        
        # Verify no exceptions occurred
        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) == 0, f"Got {len(exceptions)} exceptions during concurrent ops"
    
    async def test_large_content_performance(self, perf_memory):
        """Test performance with large content items."""
        # Create large text content (10KB each)
        large_content = "Large content item. " * 500  # ~10KB
        
        start_time = time.time()
        
        # Store 20 large items
        tasks = []
        for i in range(20):
            task = perf_memory.memorize(
                content=f"{large_content} Item {i}",
                memory_type=MemoryType.FACT,
                tags=[f"large-{i}"]
            )
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        # Test search on large items
        search_start = time.time()
        results = await perf_memory.recall(
            query="Large content item",
            search_type=SearchType.SEMANTIC,
            limit=10
        )
        search_elapsed = time.time() - search_start
        
        total_elapsed = time.time() - start_time
        
        # Should handle large content efficiently
        assert total_elapsed < 15.0, f"Large content ops took {total_elapsed:.2f}s, expected < 15s"
        assert search_elapsed < 2.0, f"Search on large content took {search_elapsed:.2f}s, expected < 2s"
        assert len(results) > 0, "Should find large content items"
    
    async def test_memory_usage_efficiency(self, perf_memory):
        """Test that memory usage doesn't grow excessively."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Store a significant number of memories
        for i in range(500):
            await perf_memory.memorize(
                content=f"Memory efficiency test content {i} with some additional text to make it realistic",
                memory_type=MemoryType.FACT,
                tags=["efficiency", f"batch-{i//50}"]
            )
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for 500 items)
        assert memory_increase < 100, f"Memory increased by {memory_increase:.1f}MB, expected < 100MB"
        
        # Test that search still works efficiently
        start_time = time.time()
        results = await perf_memory.recall(
            query="efficiency test",
            search_type=SearchType.SEMANTIC,
            limit=50
        )
        elapsed = time.time() - start_time
        
        assert elapsed < 1.0, f"Search after 500 items took {elapsed:.2f}s, expected < 1s"
        assert len(results) > 0, "Should still find results efficiently"