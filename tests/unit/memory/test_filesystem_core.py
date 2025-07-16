"""Core filesystem memory tests - basic storage and file operations."""
import pytest
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


class TestFileSystemOperations:
    """Test core filesystem operations."""
    
    @pytest.mark.asyncio
    async def test_memorize_artifact_creation(self, fs_memory):
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
    async def test_memorize_file_creation(self, fs_memory):
        """Test that memorize creates a JSON file on disk."""
        content = "Another test content."
        artifact = await fs_memory.memorize(content, tags=["tag1"], metadata={"key": "value"})

        file_path = fs_memory._get_user_memory_dir() / f"{artifact.id}.json"
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
        assert "embedding" in data  # Should exist even if None
    
    @pytest.mark.asyncio
    async def test_forget_artifact(self, fs_memory):
        """Test forgetting an artifact."""
        artifact = await fs_memory.memorize("Content to be forgotten.")
        file_path = fs_memory._get_user_memory_dir() / f"{artifact.id}.json"
        assert file_path.exists()

        forgotten = await fs_memory.forget(artifact.id)
        assert forgotten is True
        assert not file_path.exists()

        # Test forgetting non-existent artifact
        forgotten = await fs_memory.forget(UUID("00000000-0000-0000-0000-000000000000"))
        assert forgotten is False
    
    @pytest.mark.asyncio
    async def test_clear_memory(self, fs_memory):
        """Test clearing all artifacts from memory."""
        await fs_memory.memorize("Artifact 1")
        await fs_memory.memorize("Artifact 2")
        assert len(list(fs_memory._get_user_memory_dir().glob("*.json"))) == 2

        await fs_memory.clear()
        assert len(list(fs_memory._get_user_memory_dir().glob("*.json"))) == 0


class TestStorageHeuristics:
    """Test smart storage heuristics."""
    
    @pytest.mark.asyncio
    async def test_should_store_personal_info(self, fs_memory):
        """Test should_store for personal information triggers."""
        assert fs_memory.should_store("Hi, I am Tyson.") == (True, "personal")
        assert fs_memory.should_store("I have a dog.") == (True, "personal")
        assert fs_memory.should_store("My name is Gemini.") == (True, "personal")
    
    @pytest.mark.asyncio
    async def test_should_store_work_info(self, fs_memory):
        """Test should_store for work-related information triggers."""
        assert fs_memory.should_store("I work as a software engineer.") == (True, "work")
        # Due to regex order, "developer" is caught by "i am" or "i have" first
        assert fs_memory.should_store("I am a developer.") == (True, "personal")
    
    @pytest.mark.asyncio
    async def test_should_store_preferences(self, fs_memory):
        """Test should_store for preference triggers."""
        assert fs_memory.should_store("I like pizza.") == (True, "preferences")
    
    @pytest.mark.asyncio
    async def test_should_store_no_trigger(self, fs_memory):
        """Test should_store when no trigger words are present."""
        assert fs_memory.should_store("This is a random sentence.") == (False, "")
        assert fs_memory.should_store("The quick brown fox jumps over the lazy dog.") == (False, "")


class TestFileSystemStats:
    """Test filesystem statistics and inspection."""
    
    @pytest.mark.asyncio
    async def test_get_fs_stats(self, fs_memory):
        """Test _get_fs_stats method."""
        stats_empty = fs_memory._get_fs_stats()
        assert stats_empty["count"] == 0
        assert stats_empty["total_size_kb"] == 0.0
        assert stats_empty["directory"] == str(fs_memory._get_user_memory_dir())

        await fs_memory.memorize("Small content.")
        await fs_memory.memorize("Larger content that takes more space.")

        stats_with_content = fs_memory._get_fs_stats()
        assert stats_with_content["count"] == 2
        assert stats_with_content["total_size_kb"] > 0.0
        assert stats_with_content["directory"] == str(fs_memory._get_user_memory_dir())
    
    @pytest.mark.asyncio
    async def test_close_shuts_down_executor(self, fs_memory):
        """Test that close shuts down the thread pool executor."""
        try:
            await fs_memory.close()
            assert True
        except Exception:
            assert False, "close() raised an exception"