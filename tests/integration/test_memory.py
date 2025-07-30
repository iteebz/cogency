"""Integration tests using FileBackend with Result pattern."""

import pytest

from cogency.memory import Filesystem
from cogency.memory.types import MemoryType, SearchType


@pytest.mark.asyncio
async def test_create_read(memory_service):
    create_result = await memory_service.create(
        "I work as a software engineer at Google",
        type=MemoryType.FACT,
        tags=["work", "personal"],
    )
    assert create_result.success
    artifact = create_result.data

    assert artifact.content == "I work as a software engineer at Google"
    assert artifact.type == MemoryType.FACT
    assert "work" in artifact.tags

    read_result = await memory_service.read(query="software engineer")
    assert read_result.success
    results = read_result.data
    assert len(results) >= 1
    found = any("software engineer" in r.content for r in results)
    assert found


@pytest.mark.asyncio
async def test_memory_filtering(memory_service):
    sample_content = [
        {"content": "I love hiking", "tags": ["personal", "hobby"]},
        {"content": "Work meeting at 3pm", "tags": ["work", "schedule"]},
        {"content": "My favorite book", "tags": ["personal", "reading"]},
    ]

    for item in sample_content:
        create_result = await memory_service.create(item["content"], tags=item["tags"])
        assert create_result.success

    read_result = await memory_service.read(
        query="", search_type=SearchType.TAGS, tags=["personal"]
    )
    assert read_result.success
    results = read_result.data
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_memory_crud(memory_service):
    create_result = await memory_service.create("Test content", tags=["test"])
    assert create_result.success
    artifact = create_result.data
    assert artifact.content == "Test content"

    read_result = await memory_service.read(id=artifact.id)
    assert read_result.success
    results = read_result.data
    assert len(results) == 1
    assert results[0].content == "Test content"

    delete_result = await memory_service.delete(artifact_id=artifact.id)
    assert delete_result.success
    success = delete_result.data
    assert success is True

    read_result2 = await memory_service.read(id=artifact.id)
    assert read_result2.success
    results2 = read_result2.data
    assert len(results2) == 0


@pytest.mark.asyncio
async def test_persistence(tmp_path):
    temp_memory_dir = tmp_path / "memory"
    temp_memory_dir.mkdir()

    backend1 = Filesystem(memory_dir=str(temp_memory_dir))
    create_result = await backend1.create("persistent memory test")
    assert create_result.success

    backend2 = Filesystem(memory_dir=str(temp_memory_dir))
    read_result = await backend2.read(query="persistent memory")
    assert read_result.success
    results = read_result.data

    assert len(results) >= 1
    assert any("persistent memory test" in r.content for r in results)
