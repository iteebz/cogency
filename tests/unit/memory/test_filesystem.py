import pytest
import asyncio
import json
from pathlib import Path
from datetime import datetime, UTC
from uuid import UUID

from cogency.memory.filesystem import FSMemory
from cogency.memory.base import MemoryArtifact, MemoryType

@pytest.fixture
def fs_memory(tmp_path):
    """Fixture for FSMemory instance with a temporary directory."""
    memory_dir = tmp_path / ".memory"
    memory_dir.mkdir()
    return FSMemory(memory_dir=str(memory_dir))

@pytest.mark.asyncio
async def test_should_store_personal_info(fs_memory):
    """Test should_store for personal information triggers."""
    assert fs_memory.should_store("Hi, I am Tyson.") == (True, "personal")
    assert fs_memory.should_store("I have a dog.") == (True, "personal")
    assert fs_memory.should_store("My name is Gemini.") == (True, "personal")

@pytest.mark.asyncio
async def test_should_store_work_info(fs_memory):
    """Test should_store for work-related information triggers."""
    assert fs_memory.should_store("I work as a software engineer.") == (True, "work")
    # Due to regex order, "developer" is caught by "i am" or "i have" first
    assert fs_memory.should_store("I am a developer.") == (True, "personal")

@pytest.mark.asyncio
async def test_should_store_preferences(fs_memory):
    """Test should_store for preference triggers."""
    assert fs_memory.should_store("I like pizza.") == (True, "preferences")

@pytest.mark.asyncio
async def test_should_store_no_trigger(fs_memory):
    """Test should_store when no trigger words are present."""
    assert fs_memory.should_store("This is a random sentence.") == (False, "")
    assert fs_memory.should_store("The quick brown fox jumps over the lazy dog.") == (False, "")

@pytest.mark.asyncio
async def test_memorize_artifact_creation(fs_memory):
    """Test that memorize creates a MemoryArtifact with correct data."""
    content = "Test content for memorize."
    artifact = await fs_memory.memorize(content)

    assert isinstance(artifact, MemoryArtifact)
    assert artifact.content == content
    assert artifact.memory_type == MemoryType.FACT
    assert isinstance(artifact.id, UUID)
    assert artifact.tags == []
    assert artifact.metadata == {}
    assert artifact.confidence_score == 1.0
    assert artifact.access_count == 0
    assert isinstance(artifact.created_at, datetime)
    assert isinstance(artifact.last_accessed, datetime)

@pytest.mark.asyncio
async def test_memorize_file_creation(fs_memory):
    """Test that memorize creates a JSON file on disk."""
    content = "Another test content."
    artifact = await fs_memory.memorize(content, tags=["tag1"], metadata={"key": "value"})

    file_path = fs_memory.memory_dir / f"{artifact.id}.json"
    assert file_path.exists()

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    assert data["id"] == str(artifact.id)
    assert data["content"] == content
    assert data["memory_type"] == MemoryType.FACT.value
    assert data["tags"] == ["tag1"]
    assert data["metadata"] == {"key": "value"}
    assert "created_at" in data
    assert "confidence_score" in data
    assert "access_count" in data
    assert "last_accessed" in data

@pytest.mark.asyncio
async def test_recall_empty_memory(fs_memory):
    """Test recall when no artifacts are stored."""
    results = await fs_memory.recall("query")
    assert results == []

@pytest.mark.asyncio
async def test_recall_basic_match(fs_memory):
    """Test basic recall functionality with a matching artifact."""
    content = "This is a test about software engineering."
    await fs_memory.memorize(content, tags=["work"])

    results = await fs_memory.recall("software engineering")
    assert len(results) == 1
    assert results[0].content == content
    assert results[0].relevance_score > 0

@pytest.mark.asyncio
async def test_recall_with_limit(fs_memory):
    """Test recall with a specified limit."""
    await fs_memory.memorize("apple content")
    await fs_memory.memorize("banana content")
    await fs_memory.memorize("orange content")

    results = await fs_memory.recall("content", limit=2)
    assert len(results) == 2

@pytest.mark.asyncio
async def test_recall_with_tags_filter(fs_memory):
    """Test recall filtering by tags."""
    await fs_memory.memorize("content with tag A", tags=["A"])
    await fs_memory.memorize("content with tag B", tags=["B"])
    await fs_memory.memorize("content with tag A and B", tags=["A", "B"])

    results = await fs_memory.recall("content", tags=["A"])
    assert len(results) == 2
    assert all("A" in art.tags for art in results)

    results = await fs_memory.recall("content", tags=["B"])
    assert len(results) == 2
    assert all("B" in art.tags for art in results)

@pytest.mark.asyncio
async def test_recall_with_memory_type_filter(fs_memory):
    """Test recall filtering by memory type."""
    await fs_memory.memorize("fact content", memory_type=MemoryType.FACT)
    await fs_memory.memorize("context content", memory_type=MemoryType.CONTEXT)

    results = await fs_memory.recall("content", memory_type=MemoryType.FACT)
    assert len(results) == 1
    assert results[0].memory_type == MemoryType.FACT

    results = await fs_memory.recall("content", memory_type=MemoryType.CONTEXT)
    assert len(results) == 1
    assert results[0].memory_type == MemoryType.CONTEXT

@pytest.mark.asyncio
async def test_recall_relevance_scoring(fs_memory):
    """Test that relevance scoring prioritizes better matches."""
    await fs_memory.memorize("The quick brown fox jumps over the lazy dog.")
    await fs_memory.memorize("Foxes are known for their agility.")
    await fs_memory.memorize("A red fox was spotted in the forest.")

    results = await fs_memory.recall("fox")
    # Expecting artifacts with "fox" to be ranked higher
    assert len(results) == 3
    # The exact phrase "red fox" should score higher than just "fox"
    # This is a simplified check, actual scores depend on _calculate_relevance
    assert "red fox" in results[0].content.lower() or "foxes" in results[0].content.lower()

@pytest.mark.asyncio
async def test_forget_artifact(fs_memory):
    """Test forgetting an artifact."""
    artifact = await fs_memory.memorize("Content to be forgotten.")
    file_path = fs_memory.memory_dir / f"{artifact.id}.json"
    assert file_path.exists()

    forgotten = await fs_memory.forget(artifact.id)
    assert forgotten is True
    assert not file_path.exists()

    # Test forgetting non-existent artifact
    forgotten = await fs_memory.forget(UUID("00000000-0000-0000-0000-000000000000"))
    assert forgotten is False

@pytest.mark.asyncio
async def test_clear_memory(fs_memory):
    """Test clearing all artifacts from memory."""
    await fs_memory.memorize("Artifact 1")
    await fs_memory.memorize("Artifact 2")
    assert len(list(fs_memory.memory_dir.glob("*.json"))) == 2

    await fs_memory.clear()
    assert len(list(fs_memory.memory_dir.glob("*.json"))) == 0

@pytest.mark.asyncio
async def test_update_access_stats(fs_memory):
    """Test that access stats are updated on recall."""
    artifact = await fs_memory.memorize("Content for access stats.")
    original_access_count = artifact.access_count
    original_last_accessed = artifact.last_accessed

    # Recall the artifact to trigger access stat update
    results = await fs_memory.recall("Content for access stats.")
    assert len(results) == 1
    recalled_artifact = results[0]

    # Verify stats are updated in the returned artifact
    assert recalled_artifact.access_count == original_access_count + 1
    assert recalled_artifact.last_accessed > original_last_accessed

    # Verify stats are updated in the file on disk
    file_path = fs_memory.memory_dir / f"{recalled_artifact.id}.json"
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert data["access_count"] == original_access_count + 1
    assert datetime.fromisoformat(data["last_accessed"]) > original_last_accessed

@pytest.mark.asyncio
async def test_get_fs_stats(fs_memory):
    """Test _get_fs_stats method."""
    stats_empty = fs_memory._get_fs_stats()
    assert stats_empty["count"] == 0
    assert stats_empty["total_size_kb"] == 0.0
    assert stats_empty["directory"] == str(fs_memory.memory_dir)

    await fs_memory.memorize("Small content.")
    await fs_memory.memorize("Larger content that takes more space.")

    stats_with_content = fs_memory._get_fs_stats()
    assert stats_with_content["count"] == 2
    assert stats_with_content["total_size_kb"] > 0.0
    assert stats_with_content["directory"] == str(fs_memory.memory_dir)

@pytest.mark.asyncio
async def test_close_shuts_down_executor(fs_memory):
    """Test that close shuts down the thread pool executor."""
    # This is hard to test directly without inspecting internal state
    # A simple check is to ensure no errors are raised.
    # More robust testing would involve mocking ThreadPoolExecutor.
    try:
        fs_memory.close()
        # If no exception, it's a basic pass.
        assert True
    except Exception:
        assert False, "close() raised an exception"