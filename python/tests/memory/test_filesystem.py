"""Tests for filesystem memory backend."""
import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from uuid import UUID

from cogency.memory.filesystem import FSMemory
from cogency.memory.base import MemoryArtifact


@pytest.fixture
def temp_memory_dir():
    """Create temporary directory for memory tests."""
    temp_dir = tempfile.mkdtemp(prefix="cogency_memory_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def fs_memory(temp_memory_dir):
    """Create FSMemory instance with temporary directory."""
    return FSMemory(temp_memory_dir)


@pytest.mark.asyncio
async def test_memorize_basic(fs_memory):
    """Test basic memorize functionality."""
    content = "Test memory content"
    
    artifact = await fs_memory.memorize(content)
    
    assert isinstance(artifact, MemoryArtifact)
    assert artifact.content == content
    assert len(artifact.tags) == 0
    assert len(artifact.metadata) == 0
    assert isinstance(artifact.id, UUID)


@pytest.mark.asyncio
async def test_memorize_with_tags_and_metadata(fs_memory):
    """Test memorize with tags and metadata."""
    content = "Tagged memory content"
    tags = ["test", "memory", "important"]
    metadata = {"priority": "high", "category": "testing"}
    
    artifact = await fs_memory.memorize(content, tags, metadata)
    
    assert artifact.content == content
    assert artifact.tags == tags
    assert artifact.metadata == metadata


@pytest.mark.asyncio
async def test_memorize_creates_file(fs_memory, temp_memory_dir):
    """Test that memorize creates JSON file."""
    content = "File creation test"
    
    artifact = await fs_memory.memorize(content)
    
    # Check file was created
    file_path = Path(temp_memory_dir) / f"{artifact.id}.json"
    assert file_path.exists()
    assert file_path.is_file()


@pytest.mark.asyncio
async def test_recall_by_content(fs_memory):
    """Test recalling artifacts by content search."""
    # Store multiple artifacts
    await fs_memory.memorize("Python programming tips")
    await fs_memory.memorize("JavaScript best practices")
    await fs_memory.memorize("Python data structures")
    
    # Search for Python content
    results = await fs_memory.recall("Python")
    
    assert len(results) == 2
    for result in results:
        assert "Python" in result.content


@pytest.mark.asyncio
async def test_recall_by_tags(fs_memory):
    """Test recalling artifacts by tag search."""
    # Store artifacts with different tags
    await fs_memory.memorize("Content 1", tags=["python", "programming"])
    await fs_memory.memorize("Content 2", tags=["javascript", "web"])
    await fs_memory.memorize("Content 3", tags=["python", "data"])
    
    # Search by tag
    results = await fs_memory.recall("python")
    
    assert len(results) == 2
    for result in results:
        assert "python" in result.tags


@pytest.mark.asyncio
async def test_recall_with_tag_filter(fs_memory):
    """Test recalling with tag filtering."""
    # Store artifacts
    await fs_memory.memorize("Python content", tags=["python", "basic"])
    await fs_memory.memorize("Python advanced", tags=["python", "advanced"])
    await fs_memory.memorize("JavaScript content", tags=["javascript", "basic"])
    
    # Search with tag filter
    results = await fs_memory.recall("content", tags=["python"])
    
    assert len(results) == 1
    assert results[0].content == "Python content"


@pytest.mark.asyncio
async def test_recall_with_limit(fs_memory):
    """Test recall with result limit."""
    # Store multiple artifacts
    for i in range(5):
        await fs_memory.memorize(f"Test content {i}", tags=["test"])
    
    # Search with limit
    results = await fs_memory.recall("Test", limit=3)
    
    assert len(results) == 3


@pytest.mark.asyncio
async def test_recall_order_by_recency(fs_memory):
    """Test that recall orders by most recent first."""
    # Store artifacts with slight delay
    artifact1 = await fs_memory.memorize("First content")
    await asyncio.sleep(0.01)  # Small delay to ensure different timestamps
    artifact2 = await fs_memory.memorize("Second content")
    
    # Search should return most recent first
    results = await fs_memory.recall("content")
    
    assert len(results) == 2
    assert results[0].id == artifact2.id  # Most recent first
    assert results[1].id == artifact1.id


@pytest.mark.asyncio
async def test_recall_empty_results(fs_memory):
    """Test recall with no matching results."""
    await fs_memory.memorize("Some content", tags=["test"])
    
    results = await fs_memory.recall("nonexistent")
    
    assert len(results) == 0


@pytest.mark.asyncio
async def test_forget_artifact(fs_memory, temp_memory_dir):
    """Test forgetting (deleting) an artifact."""
    content = "Content to be forgotten"
    artifact = await fs_memory.memorize(content)
    
    # Verify file exists
    file_path = Path(temp_memory_dir) / f"{artifact.id}.json"
    assert file_path.exists()
    
    # Forget the artifact
    result = await fs_memory.forget(artifact.id)
    
    assert result is True
    assert not file_path.exists()


@pytest.mark.asyncio
async def test_forget_nonexistent_artifact(fs_memory):
    """Test forgetting a non-existent artifact."""
    from uuid import uuid4
    
    result = await fs_memory.forget(uuid4())
    
    assert result is False


@pytest.mark.asyncio
async def test_clear_memory(fs_memory, temp_memory_dir):
    """Test clearing all memory artifacts."""
    # Store multiple artifacts
    for i in range(3):
        await fs_memory.memorize(f"Content {i}")
    
    # Verify files exist
    json_files = list(Path(temp_memory_dir).glob("*.json"))
    assert len(json_files) == 3
    
    # Clear memory
    await fs_memory.clear()
    
    # Verify all files are gone
    json_files = list(Path(temp_memory_dir).glob("*.json"))
    assert len(json_files) == 0


@pytest.mark.asyncio
async def test_parallel_operations(fs_memory):
    """Test parallel memorize and recall operations."""
    # Store initial data
    await fs_memory.memorize("Initial content", tags=["initial"])
    
    # Parallel operations
    memorize_task = fs_memory.memorize("New content", tags=["new"])
    recall_task = fs_memory.recall("content")
    
    memorize_result, recall_result = await asyncio.gather(
        memorize_task,
        recall_task
    )
    
    assert isinstance(memorize_result, MemoryArtifact)
    assert memorize_result.content == "New content"
    assert len(recall_result) >= 1  # Should find at least the initial content


@pytest.mark.asyncio
async def test_corrupted_file_handling(fs_memory, temp_memory_dir):
    """Test handling of corrupted JSON files."""
    # Create a corrupted JSON file
    corrupted_file = Path(temp_memory_dir) / "corrupted.json"
    corrupted_file.write_text("invalid json content")
    
    # Store valid artifact
    await fs_memory.memorize("Valid content")
    
    # Recall should skip corrupted file and return valid results
    results = await fs_memory.recall("content")
    
    assert len(results) == 1
    assert results[0].content == "Valid content"