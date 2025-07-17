"""Unit tests for smart memory functionality."""
import pytest
from cogency.memory.backends.filesystem import FilesystemBackend
from cogency.tools.recall import RecallTool


@pytest.fixture
async def memory(fs_memory_instance):
    """Create a test memory instance."""
    return fs_memory_instance


def test_should_store_personal_info(memory):
    """Test smart auto-storage heuristics."""
    # Personal triggers
    assert memory.should_store("I have ADHD") == (True, "personal")
    assert memory.should_store("I am a developer") == (True, "personal")
    assert memory.should_store("My name is John") == (True, "personal")
    
    # Work triggers
    assert memory.should_store("I work at Google") == (True, "work")
    assert memory.should_store("I'm a software engineer") == (True, "work")
    
    # Preferences
    assert memory.should_store("I like quiet environments") == (True, "preferences")
    
    # Should not store
    assert memory.should_store("What's the weather today?") == (False, "")
    assert memory.should_store("Hello there") == (False, "")


@pytest.mark.asyncio
async def test_memory_storage_and_recall(memory):
    """Test basic memory storage and recall."""
    # Store personal info
    artifact = await memory.memorize("I have ADHD and work as a software engineer", tags=["personal"])
    assert artifact.content == "I have ADHD and work as a software engineer"
    assert "personal" in artifact.tags
    
    # Recall with partial match
    results = await memory.recall("work situation")
    assert len(results) == 1
    assert "software engineer" in results[0].content
    
    # Recall with exact word
    results = await memory.recall("ADHD")
    assert len(results) == 1
    assert "ADHD" in results[0].content


@pytest.mark.asyncio
async def test_memory_tools(memory):
    """Test memory tools with smart auto-tagging."""
    memorize_tool = MemorizeTool(memory)
    recall_tool = RecallTool(memory)
    
    # Test memorize with auto-tagging
    result = await memorize_tool.run(content="I have ADHD and work as a software engineer")
    assert result["success"] is True
    assert "personal" in result["tags"]
    
    # Test recall
    result = await recall_tool.run(query="work situation")
    assert result["success"] is True
    assert result["results_count"] == 1
    assert "software engineer" in result["results"][0]["content"]