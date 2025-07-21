"""Test memory backend business logic."""

import pytest

from cogency.memory.core import MemoryType, SearchType


@pytest.mark.asyncio
async def test_memory_create_read(memory_backend):
    """Test memory creation and retrieval."""
    # Store memory
    artifact = await memory_backend.create(
        "I work as a software engineer at Google",
        memory_type=MemoryType.FACT,
        tags=["work", "personal"],
    )

    assert artifact.content == "I work as a software engineer at Google"
    assert artifact.memory_type == MemoryType.FACT
    assert "work" in artifact.tags

    # Retrieve by text search
    results = await memory_backend.read(query="software engineer")
    assert len(results) >= 1
    found = any("software engineer" in r.content for r in results)
    assert found


@pytest.mark.asyncio
async def test_memory_filtering(memory_backend, sample_memory_content):
    """Test memory filtering by tags."""
    # Store sample data
    for item in sample_memory_content:
        await memory_backend.create(item["content"], tags=item["tags"])

    # Filter by tags
    results = await memory_backend.read(query="", search_type=SearchType.TAGS, tags=["personal"])
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_memory_crud(memory_backend):
    """Test CRUD operations."""
    # CREATE
    artifact = await memory_backend.create("Test content", tags=["test"])
    assert artifact.content == "Test content"

    # READ by ID
    results = await memory_backend.read(artifact_id=artifact.id)
    assert len(results) == 1
    assert results[0].content == "Test content"

    # DELETE
    success = await memory_backend.delete(artifact_id=artifact.id)
    assert success is True

    # Verify deletion
    results = await memory_backend.read(artifact_id=artifact.id)
    assert len(results) == 0


@pytest.mark.asyncio
async def test_memory_persistence(temp_memory_dir):
    """Test memory persists across backend instances."""
    from cogency.memory.backends.filesystem import FileBackend

    # Store with first instance
    backend1 = FileBackend(memory_dir=temp_memory_dir)
    await backend1.create("persistent memory test")

    # New instance should find it
    backend2 = FileBackend(memory_dir=temp_memory_dir)
    results = await backend2.read(query="persistent memory")

    assert len(results) >= 1
    assert any("persistent memory test" in r.content for r in results)
