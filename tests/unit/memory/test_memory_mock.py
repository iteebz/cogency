"""MockBackend tests with Result pattern support."""

from typing import Any, Dict, List, Optional
from uuid import UUID

import pytest
from resilient_result import Result

from cogency.memory.backends.base import BaseBackend
from cogency.memory.core import Memory, MemoryType


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

    async def _read_by_id(self, artifact_id: UUID) -> List[Memory]:
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

    async def _update(self, artifact_id: UUID, updates: Dict[str, Any]) -> bool:
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

    async def _delete_by_id(self, artifact_id: UUID) -> bool:
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

    async def _embed(self, content: str) -> Optional[List[float]]:
        return None


@pytest.fixture
def mock_backend():
    return MockBackend()


@pytest.mark.asyncio
async def test_create(mock_backend):
    result = await mock_backend.create("Test content")

    assert result.success
    artifact = result.data
    assert isinstance(artifact, Memory)
    assert artifact.content == "Test content"
    assert artifact.id in mock_backend.artifacts
    assert mock_backend.ready_called


@pytest.mark.asyncio
async def test_read_by_id(mock_backend):
    create_result = await mock_backend.create("Test")
    assert create_result.success
    memory = create_result.data

    read_result = await mock_backend.read(artifact_id=memory.id)
    assert read_result.success
    results = read_result.data

    assert len(results) == 1
    assert results[0].content == "Test"


@pytest.mark.asyncio
async def test_read_all(mock_backend):
    create1_result = await mock_backend.create("Content 1")
    assert create1_result.success
    create2_result = await mock_backend.create("Content 2")
    assert create2_result.success

    read_result = await mock_backend.read()
    assert read_result.success
    results = read_result.data

    assert len(results) == 2


@pytest.mark.asyncio
async def test_update(mock_backend):
    create_result = await mock_backend.create("Original")
    assert create_result.success
    memory = create_result.data

    update_result = await mock_backend.update(memory.id, {"content": "Updated"})
    assert update_result.success
    success = update_result.data

    assert success is True
    updated = mock_backend.artifacts[memory.id]
    assert updated.content == "Updated"


@pytest.mark.asyncio
async def test_delete_by_id(mock_backend):
    create_result = await mock_backend.create("Test")
    assert create_result.success
    memory = create_result.data

    delete_result = await mock_backend.delete(artifact_id=memory.id)
    assert delete_result.success
    success = delete_result.data

    assert success is True
    assert memory.id not in mock_backend.artifacts


@pytest.mark.asyncio
async def test_delete_all(mock_backend):
    create1_result = await mock_backend.create("Test 1")
    assert create1_result.success
    create2_result = await mock_backend.create("Test 2")
    assert create2_result.success

    delete_result = await mock_backend.delete(delete_all=True)
    assert delete_result.success
    success = delete_result.data

    assert success is True
    assert len(mock_backend.artifacts) == 0


def test_memory_backend_interface():
    from cogency.memory.backends.base import MemoryBackend

    with pytest.raises(TypeError):
        MemoryBackend()


def test_abstract_methods():
    from cogency.memory.backends.base import MemoryBackend

    class IncompleteBackend(MemoryBackend):
        pass

    with pytest.raises(TypeError):
        IncompleteBackend()


@pytest.mark.asyncio
async def test_by_type(mock_backend):
    fact = Memory(content="Fact", memory_type=MemoryType.FACT)
    episode = Memory(content="Episode", memory_type=MemoryType.EPISODIC)
    await mock_backend._store(fact, None)
    await mock_backend._store(episode, None)

    read_result = await mock_backend.read(memory_type=MemoryType.FACT)
    assert read_result.success
    results = read_result.data

    assert len(results) == 1
    assert results[0].content == "Fact"


@pytest.mark.asyncio
async def test_by_tags(mock_backend):
    tagged = Memory(content="Tagged", tags=["important"])
    untagged = Memory(content="Untagged", tags=[])
    await mock_backend._store(tagged, None)
    await mock_backend._store(untagged, None)

    read_result = await mock_backend.read(tags=["important"])
    assert read_result.success
    results = read_result.data

    assert len(results) == 1
    assert results[0].content == "Tagged"


@pytest.mark.asyncio
async def test_delete_tags(mock_backend):
    tagged = Memory(content="Tagged", tags=["remove"])
    untagged = Memory(content="Keep", tags=[])
    await mock_backend._store(tagged, None)
    await mock_backend._store(untagged, None)

    delete_result = await mock_backend.delete(tags=["remove"])
    assert delete_result.success
    success = delete_result.data

    assert success is True
    assert tagged.id not in mock_backend.artifacts
    assert untagged.id in mock_backend.artifacts
