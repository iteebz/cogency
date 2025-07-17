"""Core filesystem memory tests - basic storage and file operations."""
import pytest
import json
from pathlib import Path
from datetime import datetime, UTC
from uuid import UUID

from cogency.memory.backends.filesystem import FilesystemBackend
from cogency.memory.core import MemoryArtifact, MemoryType


@pytest.fixture
def fs_memory(tmp_path):
    """Fixture for FilesystemBackend instance with a temporary directory."""
    memory_dir = tmp_path / ".memory"
    memory_dir.mkdir()
    return FilesystemBackend(memory_dir=str(memory_dir))


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

        file_path = fs_memory.memory_dir / "default" / f"{artifact.id}.json"
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
        
        # Test that artifact can be recalled before forgetting
        results = await fs_memory.recall("forgotten")
        assert len(results) == 1
        
        forgotten = await fs_memory.forget(artifact.id)
        assert forgotten is True
        
        # Test that artifact can no longer be recalled after forgetting
        results = await fs_memory.recall("forgotten")
        assert len(results) == 0

        # Test forgetting non-existent artifact
        forgotten = await fs_memory.forget(UUID("00000000-0000-0000-0000-000000000000"))
        assert forgotten is False
    
    @pytest.mark.asyncio
    async def test_clear_memory(self, fs_memory):
        """Test clearing all artifacts from memory."""
        await fs_memory.memorize("Artifact 1")
        await fs_memory.memorize("Artifact 2")
        
        # Verify artifacts exist by checking recall results
        results = await fs_memory.recall("Artifact")
        assert len(results) == 2

        await fs_memory.clear()
        
        # Verify artifacts are cleared by checking recall results
        results = await fs_memory.recall("Artifact")
        assert len(results) == 0


