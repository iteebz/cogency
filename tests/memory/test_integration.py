"""Integration tests for memory system."""
import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path

from cogency.memory.filesystem import FSMemory
from cogency.memory.tools import MemorizeTool, RecallTool


@pytest.fixture
def temp_memory_dir():
    """Create temporary directory for integration tests."""
    temp_dir = tempfile.mkdtemp(prefix="cogency_memory_integration_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def memory_system(temp_memory_dir):
    """Create complete memory system for integration tests."""
    memory = FSMemory(temp_memory_dir)
    memorize_tool = MemorizeTool(memory)
    recall_tool = RecallTool(memory)
    return memory, memorize_tool, recall_tool


@pytest.mark.asyncio
async def test_full_memory_workflow(memory_system):
    """Test complete memory workflow: memorize -> recall -> forget."""
    memory, memorize_tool, recall_tool = memory_system
    
    # Memorize some content
    memorize_result = await memorize_tool.run(
        content="Important project meeting notes",
        tags=["meeting", "project"],
        metadata={"priority": "high", "attendees": 5}
    )
    
    assert memorize_result["success"] is True
    artifact_id = memorize_result["artifact_id"]
    
    # Recall the content
    recall_result = await recall_tool.run(query="meeting")
    
    assert recall_result["success"] is True
    assert recall_result["results_count"] == 1
    assert recall_result["results"][0]["content"] == "Important project meeting notes"
    assert recall_result["results"][0]["tags"] == ["meeting", "project"]
    
    # Verify we can forget the artifact
    from uuid import UUID
    forget_result = await memory.forget(UUID(artifact_id))
    assert forget_result is True
    
    # Verify it's gone
    recall_after_forget = await recall_tool.run(query="meeting")
    assert recall_after_forget["results_count"] == 0


@pytest.mark.asyncio
async def test_memory_tools_parallel_execution(memory_system):
    """Test parallel execution of memory tools."""
    memory, memorize_tool, recall_tool = memory_system
    
    # Store some initial data
    await memorize_tool.run(
        content="Database optimization techniques",
        tags=["database", "performance"]
    )
    
    await memorize_tool.run(
        content="API rate limiting best practices",
        tags=["api", "performance"]
    )
    
    # Execute memorize and recall in parallel
    memorize_task = memorize_tool.run(
        content="New performance insight: caching reduces latency",
        tags=["performance", "caching"]
    )
    
    recall_task = recall_tool.run(query="performance")
    
    memorize_result, recall_result = await asyncio.gather(
        memorize_task,
        recall_task
    )
    
    # Verify memorize succeeded
    assert memorize_result["success"] is True
    assert "caching" in memorize_result["tags"]
    
    # Verify recall found existing performance-related content
    assert recall_result["success"] is True
    assert recall_result["results_count"] >= 2  # At least the 2 we stored initially


@pytest.mark.asyncio
async def test_memory_search_refinement(memory_system):
    """Test progressive search refinement using tags."""
    memory, memorize_tool, recall_tool = memory_system
    
    # Store diverse content
    await memorize_tool.run(
        content="Python programming best practices",
        tags=["python", "programming", "best-practices"]
    )
    
    await memorize_tool.run(
        content="JavaScript async/await patterns",
        tags=["javascript", "programming", "async"]
    )
    
    await memorize_tool.run(
        content="Python data science libraries",
        tags=["python", "data-science", "libraries"]
    )
    
    await memorize_tool.run(
        content="Database design principles",
        tags=["database", "design", "best-practices"]
    )
    
    # Broad search
    all_programming = await recall_tool.run(query="programming")
    assert all_programming["results_count"] == 2
    
    # Refined search by content
    python_content = await recall_tool.run(query="Python")
    assert python_content["results_count"] == 2
    
    # Tag-filtered search
    python_with_tags = await recall_tool.run(query="programming", tags=["python"])
    assert python_with_tags["results_count"] == 1
    assert "best practices" in python_with_tags["results"][0]["content"]


@pytest.mark.asyncio
async def test_memory_persistence_across_instances(temp_memory_dir):
    """Test that memory persists across different FSMemory instances."""
    # First instance - store data
    memory1 = FSMemory(temp_memory_dir)
    memorize_tool1 = MemorizeTool(memory1)
    
    await memorize_tool1.run(
        content="Persistent memory test",
        tags=["persistence", "test"]
    )
    
    # Second instance - should see the same data
    memory2 = FSMemory(temp_memory_dir)
    recall_tool2 = RecallTool(memory2)
    
    results = await recall_tool2.run(query="persistent")
    
    assert results["success"] is True
    assert results["results_count"] == 1
    assert results["results"][0]["content"] == "Persistent memory test"
    assert "persistence" in results["results"][0]["tags"]


@pytest.mark.asyncio
async def test_memory_error_handling_integration(memory_system):
    """Test error handling in integrated memory system."""
    memory, memorize_tool, recall_tool = memory_system
    
    # Test memorize with missing content
    error_result = await memorize_tool.run(tags=["test"])
    assert "error" in error_result
    assert "content parameter is required" in error_result["error"]
    
    # Test recall with missing query
    error_result = await recall_tool.run(limit=5)
    assert "error" in error_result
    assert "query parameter is required" in error_result["error"]
    
    # Verify system still works after errors
    success_result = await memorize_tool.run(content="Recovery test")
    assert success_result["success"] is True


@pytest.mark.asyncio
async def test_large_scale_memory_operations(memory_system):
    """Test memory system with larger data sets."""
    memory, memorize_tool, recall_tool = memory_system
    
    # Store multiple artifacts
    for i in range(20):
        await memorize_tool.run(
            content=f"Test content item {i} with unique data",
            tags=["test", f"item-{i}", "batch-operation"],
            metadata={"batch_id": "large-scale-test", "index": i}
        )
    
    # Test broad search
    all_test_items = await recall_tool.run(query="Test content")
    assert all_test_items["results_count"] == 20
    
    # Test limited search
    limited_results = await recall_tool.run(query="Test content", limit=5)
    assert limited_results["results_count"] == 5
    
    # Test tag filtering
    specific_item = await recall_tool.run(query="content", tags=["item-10"])
    assert specific_item["results_count"] == 1
    assert "item 10" in specific_item["results"][0]["content"]


@pytest.mark.asyncio
async def test_concurrent_memory_access(memory_system):
    """Test concurrent access to memory system."""
    memory, memorize_tool, recall_tool = memory_system
    
    # Store initial content
    await memorize_tool.run(content="Concurrent test base", tags=["concurrent"])
    
    # Create multiple concurrent tasks
    tasks = []
    
    # Memorize tasks
    for i in range(5):
        task = memorize_tool.run(
            content=f"Concurrent memorize {i}",
            tags=["concurrent", f"task-{i}"]
        )
        tasks.append(task)
    
    # Recall tasks
    for i in range(3):
        task = recall_tool.run(query="concurrent")
        tasks.append(task)
    
    # Execute all tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Verify no exceptions occurred
    for result in results:
        assert not isinstance(result, Exception)
    
    # Verify final state
    final_recall = await recall_tool.run(query="concurrent")
    assert final_recall["results_count"] >= 6  # 1 initial + 5 concurrent