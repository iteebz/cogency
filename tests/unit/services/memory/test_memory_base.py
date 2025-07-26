"""Test BaseBackend - memory backend contracts and template methods."""

from typing import Any, Dict, List, Optional

import pytest

from cogency.memory.core import Memory, MemoryType
from cogency.services.memory.base import BaseBackend


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
def backend():
    return MockBackend()


class TestBaseBackendCore:
    """Test core CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_stores_artifact(self, backend):
        artifact = await backend.create("Test content")

        assert artifact is not None
        assert isinstance(artifact, Memory)
        assert artifact.content == "Test content"
        assert artifact.id in backend.artifacts
        assert backend.ready_called

    @pytest.mark.asyncio
    async def test_read_by_id_works(self, backend):
        memory_result = await backend.create("Test")
        assert memory_result is not None
        memory = memory_result
        results_result = await backend.read(artifact_id=memory.id)
        assert results_result is not None
        results = results_result

        assert len(results) == 1
        assert results[0].content == "Test"

    @pytest.mark.asyncio
    async def test_read_all_without_params(self, backend):
        create1_result = await backend.create("Content 1")
        assert create1_result is not None
        create2_result = await backend.create("Content 2")
        assert create2_result is not None

        results_result = await backend.read()
        assert results_result is not None
        results = results_result

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_update_modifies_artifact(self, backend):
        create_result = await backend.create("Original")
        memory = create_result
        success_result = await backend.update(memory.id, {"content": "Updated"})
        assert success_result is not None
        success = success_result

        assert success is True
        updated = backend.artifacts[memory.id]
        assert updated.content == "Updated"

    @pytest.mark.asyncio
    async def test_delete_by_id_removes_artifact(self, backend):
        memory_result = await backend.create("Test")
        assert memory_result is not None
        memory = memory_result
        success_result = await backend.delete(artifact_id=memory.id)
        assert success_result is not None
        success = success_result

        assert success is True
        assert memory.id not in backend.artifacts

    @pytest.mark.asyncio
    async def test_delete_all_clears_artifacts(self, backend):
        create1_result = await backend.create("Test 1")
        assert create1_result is not None
        create2_result = await backend.create("Test 2")
        assert create2_result is not None

        success_result = await backend.delete(delete_all=True)
        assert success_result is not None
        success = success_result

        assert success is True
        assert len(backend.artifacts) == 0


class TestBaseBackendAbstract:
    """Test abstract base class requirements."""

    def test_cannot_instantiate_base_backend(self):
        with pytest.raises(TypeError):
            BaseBackend()

    def test_abstract_methods_required(self):
        class IncompleteBackend(BaseBackend):
            pass

        with pytest.raises(TypeError):
            IncompleteBackend()


class TestBaseBackendFiltering:
    """Test filtering and search delegation."""

    @pytest.mark.asyncio
    async def test_reads_by_memory_type(self, backend):
        fact = Memory(content="Fact", memory_type=MemoryType.FACT)
        episode = Memory(content="Episode", memory_type=MemoryType.EPISODIC)
        await backend._store(fact, None)
        await backend._store(episode, None)

        results_result = await backend.read(memory_type=MemoryType.FACT)
        assert results_result is not None
        results = results_result

        assert len(results) == 1
        assert results[0].content == "Fact"

    @pytest.mark.asyncio
    async def test_reads_by_tags(self, backend):
        tagged = Memory(content="Tagged", tags=["important"])
        untagged = Memory(content="Untagged", tags=[])
        await backend._store(tagged, None)
        await backend._store(untagged, None)

        results_result = await backend.read(tags=["important"])
        assert results_result is not None
        results = results_result

        assert len(results) == 1
        assert results[0].content == "Tagged"

    @pytest.mark.asyncio
    async def test_delete_by_tags(self, backend):
        tagged = Memory(content="Tagged", tags=["remove"])
        untagged = Memory(content="Keep", tags=[])
        await backend._store(tagged, None)
        await backend._store(untagged, None)

        success_result = await backend.delete(tags=["remove"])
        assert success_result is not None
        success = success_result

        assert success is True
        assert tagged.id not in backend.artifacts
        assert untagged.id in backend.artifacts
