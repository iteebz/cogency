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
    assert artifact is not None

    assert artifact.content == "I work as a software engineer at Google"
    assert artifact.memory_type == MemoryType.FACT
    assert "work" in artifact.tags

    # Retrieve by text search
    results = await memory_backend.read(query="software engineer")
    assert results is not None
    assert len(results) >= 1
    found = any("software engineer" in r.content for r in results)
    assert found


@pytest.mark.asyncio
async def test_memory_filtering(memory_backend):
    """Test memory filtering by tags."""
    # Store sample data
    sample_content = [
        {"content": "I love hiking", "tags": ["personal", "hobby"]},
        {"content": "Work meeting at 3pm", "tags": ["work", "schedule"]},
        {"content": "My favorite book", "tags": ["personal", "reading"]},
    ]

    for item in sample_content:
        create_result = await memory_backend.create(item["content"], tags=item["tags"])
        assert create_result is not None

    # Filter by tags
    results = await memory_backend.read(query="", search_type=SearchType.TAGS, tags=["personal"])
    assert results is not None
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
async def test_persistence(tmp_path):
    """Test memory persists across backend instances."""
    from cogency.services.memory.filesystem import FileBackend

    # Use pytest's tmp_path fixture
    temp_memory_dir = tmp_path / "memory"
    temp_memory_dir.mkdir()

    # Store with first instance
    backend1 = FileBackend(memory_dir=str(temp_memory_dir))
    await backend1.create("persistent memory test")

    # New instance should find it
    backend2 = FileBackend(memory_dir=str(temp_memory_dir))
    results = await backend2.read(query="persistent memory")

    assert len(results) >= 1
    assert any("persistent memory test" in r.content for r in results)
