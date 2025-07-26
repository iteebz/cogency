"""Comprehensive memory system tests - types, backends, and business logic."""

import time
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

import pytest

from cogency.memory.core import Memory, MemoryType, SearchType
from cogency.services.memory.base import BaseBackend
from cogency.services.memory.filesystem import FileBackend


class MockBackend(BaseBackend):
    """Minimal concrete backend for testing."""

    def __init__(self, embedder=None):
        super().__init__(embedder)
        self.artifacts = {}
        self.ready_called = False

    async def _ready(self) -> None:
        self.ready_called = True

    async def _store(self, artifact: Memory, embedding: Optional[List[float]], **kwargs) -> None:
        self.artifacts[artifact.id] = artifact

    async def _read_by_id(self, artifact_id) -> List[Memory]:
        return [self.artifacts[artifact_id]] if artifact_id in self.artifacts else []

    async def _read(self, memory_type=None, tags=None, filters=None, **kwargs) -> List[Memory]:
        results = []
        for artifact in self.artifacts.values():
            if memory_type and artifact.memory_type != memory_type:
                continue
            if tags and not any(tag in artifact.tags for tag in tags):
                continue
            results.append(artifact)
        return results

    async def _update(self, artifact_id, updates: Dict[str, Any]) -> bool:
        if artifact_id in self.artifacts:
            artifact = self.artifacts[artifact_id]
            for key, value in updates.items():
                if hasattr(artifact, key):
                    setattr(artifact, key, value)
            return True
        return False

    async def _delete_all(self) -> bool:
        self.artifacts.clear()
        return True

    async def _delete_by_id(self, artifact_id) -> bool:
        return bool(self.artifacts.pop(artifact_id, None))

    async def _delete_by_filters(
        self, tags: Optional[List[str]], filters: Optional[Dict[str, Any]]
    ) -> bool:
        to_delete = []
        for artifact_id, artifact in self.artifacts.items():
            if tags and any(tag in artifact.tags for tag in tags):
                to_delete.append(artifact_id)

        for artifact_id in to_delete:
            self.artifacts.pop(artifact_id)

        return len(to_delete) > 0


@pytest.fixture
def mock_backend():
    return MockBackend()


def test_memory_creation():
    memory = Memory(content="test memory", memory_type=MemoryType.FACT, tags=["test"])

    assert memory.content == "test memory"
    assert memory.memory_type == MemoryType.FACT
    assert "test" in memory.tags
    assert memory.id is not None
    assert isinstance(memory.created_at, datetime)


def test_decay_score():
    memory = Memory(content="test", confidence_score=1.0)

    score = memory.decay()
    assert 0.8 < score <= 1.0


def test_access_tracking():
    memory = Memory(content="test")

    initial_count = memory.access_count
    initial_accessed = memory.last_accessed

    time.sleep(0.001)
    memory.access_count += 1
    memory.last_accessed = datetime.now(UTC)

    assert memory.access_count == initial_count + 1
    assert memory.last_accessed > initial_accessed


def test_type_enum():
    assert MemoryType.FACT
    assert MemoryType.EPISODIC
    assert MemoryType.EXPERIENCE

    fact = Memory(content="fact", memory_type=MemoryType.FACT)
    episodic = Memory(content="episodic", memory_type=MemoryType.EPISODIC)
    experience = Memory(content="experience", memory_type=MemoryType.EXPERIENCE)

    assert fact.memory_type == MemoryType.FACT
    assert episodic.memory_type == MemoryType.EPISODIC
    assert experience.memory_type == MemoryType.EXPERIENCE


@pytest.mark.asyncio
async def test_create(mock_backend):
    artifact = await mock_backend.create("Test content")

    assert artifact is not None
    assert isinstance(artifact, Memory)
    assert artifact.content == "Test content"
    assert artifact.id in mock_backend.artifacts
    assert mock_backend.ready_called


@pytest.mark.asyncio
async def test_read_by_id(mock_backend):
    memory_result = await mock_backend.create("Test")
    assert memory_result is not None
    memory = memory_result
    results_result = await mock_backend.read(artifact_id=memory.id)
    assert results_result is not None
    results = results_result

    assert len(results) == 1
    assert results[0].content == "Test"


@pytest.mark.asyncio
async def test_read_all(mock_backend):
    create1_result = await mock_backend.create("Content 1")
    assert create1_result is not None
    create2_result = await mock_backend.create("Content 2")
    assert create2_result is not None

    results_result = await mock_backend.read()
    assert results_result is not None
    results = results_result

    assert len(results) == 2


@pytest.mark.asyncio
async def test_update(mock_backend):
    create_result = await mock_backend.create("Original")
    memory = create_result
    success_result = await mock_backend.update(memory.id, {"content": "Updated"})
    assert success_result is not None
    success = success_result

    assert success is True
    updated = mock_backend.artifacts[memory.id]
    assert updated.content == "Updated"


@pytest.mark.asyncio
async def test_delete_by_id(mock_backend):
    memory_result = await mock_backend.create("Test")
    assert memory_result is not None
    memory = memory_result
    success_result = await mock_backend.delete(artifact_id=memory.id)
    assert success_result is not None
    success = success_result

    assert success is True
    assert memory.id not in mock_backend.artifacts


@pytest.mark.asyncio
async def test_delete_all(mock_backend):
    create1_result = await mock_backend.create("Test 1")
    assert create1_result is not None
    create2_result = await mock_backend.create("Test 2")
    assert create2_result is not None

    success_result = await mock_backend.delete(delete_all=True)
    assert success_result is not None
    success = success_result

    assert success is True
    assert len(mock_backend.artifacts) == 0


def test_base_backend():
    with pytest.raises(TypeError):
        BaseBackend()


def test_abstract_methods():
    class IncompleteBackend(BaseBackend):
        pass

    with pytest.raises(TypeError):
        IncompleteBackend()


@pytest.mark.asyncio
async def test_by_type(mock_backend):
    fact = Memory(content="Fact", memory_type=MemoryType.FACT)
    episode = Memory(content="Episode", memory_type=MemoryType.EPISODIC)
    await mock_backend._store(fact, None)
    await mock_backend._store(episode, None)

    results_result = await mock_backend.read(memory_type=MemoryType.FACT)
    assert results_result is not None
    results = results_result

    assert len(results) == 1
    assert results[0].content == "Fact"


@pytest.mark.asyncio
async def test_by_tags(mock_backend):
    tagged = Memory(content="Tagged", tags=["important"])
    untagged = Memory(content="Untagged", tags=[])
    await mock_backend._store(tagged, None)
    await mock_backend._store(untagged, None)

    results_result = await mock_backend.read(tags=["important"])
    assert results_result is not None
    results = results_result

    assert len(results) == 1
    assert results[0].content == "Tagged"


@pytest.mark.asyncio
async def test_delete_tags(mock_backend):
    tagged = Memory(content="Tagged", tags=["remove"])
    untagged = Memory(content="Keep", tags=[])
    await mock_backend._store(tagged, None)
    await mock_backend._store(untagged, None)

    success_result = await mock_backend.delete(tags=["remove"])
    assert success_result is not None
    success = success_result

    assert success is True
    assert tagged.id not in mock_backend.artifacts
    assert untagged.id in mock_backend.artifacts


@pytest.mark.asyncio
async def test_create_read(memory_service):
    artifact = await memory_service.create(
        "I work as a software engineer at Google",
        memory_type=MemoryType.FACT,
        tags=["work", "personal"],
    )
    assert artifact is not None

    assert artifact.content == "I work as a software engineer at Google"
    assert artifact.memory_type == MemoryType.FACT
    assert "work" in artifact.tags

    results = await memory_service.read(query="software engineer")
    assert results is not None
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
        assert create_result is not None

    results = await memory_service.read(query="", search_type=SearchType.TAGS, tags=["personal"])
    assert results is not None
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_memory_crud(memory_service):
    artifact = await memory_service.create("Test content", tags=["test"])
    assert artifact.content == "Test content"

    results = await memory_service.read(artifact_id=artifact.id)
    assert len(results) == 1
    assert results[0].content == "Test content"

    success = await memory_service.delete(artifact_id=artifact.id)
    assert success is True

    results = await memory_service.read(artifact_id=artifact.id)
    assert len(results) == 0


@pytest.mark.asyncio
async def test_persistence(tmp_path):
    temp_memory_dir = tmp_path / "memory"
    temp_memory_dir.mkdir()

    backend1 = FileBackend(memory_dir=str(temp_memory_dir))
    await backend1.create("persistent memory test")

    backend2 = FileBackend(memory_dir=str(temp_memory_dir))
    results = await backend2.read(query="persistent memory")

    assert len(results) >= 1
    assert any("persistent memory test" in r.content for r in results)
