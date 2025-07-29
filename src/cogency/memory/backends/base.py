"""Memory backend interface and shared implementation."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import UUID

from resilient_result import Result, Retry, resilient

from cogency.memory.core import Memory, MemoryType, SearchType
from cogency.memory.search import search

# Singleton instance for default memory backend
_memory_instance = None


class MemoryBackend(ABC):
    """Interface that all memory backends must implement."""

    def __init__(self, embedder=None):
        self.embedder = embedder

    @abstractmethod
    async def create(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.FACT,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Result:
        """CREATE - Store new content in memory."""
        pass

    @abstractmethod
    async def read(
        self,
        query: str = None,
        artifact_id: UUID = None,
        search_type: SearchType = SearchType.AUTO,
        limit: int = 10,
        threshold: float = 0.7,
        tags: Optional[List[str]] = None,
        memory_type: Optional[MemoryType] = None,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Result:
        """READ - Retrieve memories from storage."""
        pass

    @abstractmethod
    async def update(self, artifact_id: UUID, updates: Dict[str, Any]) -> Result:
        """UPDATE - Modify existing memory."""
        pass

    @abstractmethod
    async def delete(
        self,
        artifact_id: UUID = None,
        tags: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        delete_all: bool = False,
    ) -> Result:
        """DELETE - Remove memories from storage."""
        pass


class BaseBackend(MemoryBackend):
    """Shared implementation for concrete backends."""

    @resilient(retry=Retry.api())
    async def create(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.FACT,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Result:
        """CREATE - Standard artifact creation with storage delegation."""
        await self._ready()

        artifact = Memory(
            content=content,
            memory_type=memory_type,
            tags=tags or [],
            metadata=metadata or {},
        )

        embedding = await self._embed(content)
        await self._store(artifact, embedding, **kwargs)
        return Result.ok(artifact)

    @resilient(retry=Retry.api())
    async def read(
        self,
        query: str = None,
        artifact_id: UUID = None,
        search_type: SearchType = SearchType.AUTO,
        limit: int = 10,
        threshold: float = 0.7,
        tags: Optional[List[str]] = None,
        memory_type: Optional[MemoryType] = None,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Result:
        """READ - Unified retrieval with storage delegation."""
        await self._ready()

        # Read by specific artifact_id
        if artifact_id:
            results = await self._read_by_id(artifact_id)
            return Result.ok(results)

        # No query - return filtered artifacts
        if not query:
            results = await self._read(
                memory_type=memory_type, tags=tags, filters=filters, **kwargs
            )
            return Result.ok(results)

        # Query-based search with storage-specific optimizations
        if self._has_search(search_type):
            results = await self._search(
                query,
                search_type,
                limit,
                threshold,
                tags,
                memory_type,
                filters,
                **kwargs,
            )
            return Result.ok(results)

        # Fallback to search module
        artifacts = await self._read(memory_type=memory_type, tags=tags, filters=filters, **kwargs)

        if not artifacts:
            return Result.ok([])

        results = await search(
            query,
            artifacts,
            search_type,
            threshold,
            self.embedder,
            self._embed,
        )
        return Result.ok(results[:limit])

    @resilient(retry=Retry.api())
    async def update(self, artifact_id: UUID, updates: Dict[str, Any]) -> Result:
        """UPDATE - Standard update logic with storage delegation."""
        await self._ready()

        # Filter internal keys
        clean_updates = {k: v for k, v in updates.items() if k != "user_id"}
        if not clean_updates:
            return Result.ok(True)

        success = await self._update(artifact_id, clean_updates)
        return Result.ok(success)

    @resilient(retry=Retry.api())
    async def delete(
        self,
        artifact_id: UUID = None,
        tags: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        delete_all: bool = False,
    ) -> Result:
        """DELETE - Unified deletion with storage delegation."""
        await self._ready()

        if delete_all:
            success = await self._delete_all()
        elif artifact_id:
            success = await self._delete_by_id(artifact_id)
        elif tags or filters:
            success = await self._delete_by_filters(tags, filters)
        else:
            success = False

        return Result.ok(success)

    # Storage primitives - implement these in subclasses

    @abstractmethod
    async def _ready(self) -> None:
        """Ensure backend is initialized and ready."""
        pass

    @abstractmethod
    async def _store(self, artifact: Memory, embedding: Optional[List[float]], **kwargs) -> None:
        """Store artifact with embedding."""
        pass

    @abstractmethod
    async def _read_by_id(self, artifact_id: UUID) -> List[Memory]:
        """Read single artifact by ID."""
        pass

    @abstractmethod
    async def _read(
        self,
        memory_type: Optional[MemoryType] = None,
        tags: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> List[Memory]:
        """Read filtered artifacts."""
        pass

    @abstractmethod
    async def _update(self, artifact_id: UUID, updates: Dict[str, Any]) -> bool:
        """Update artifact with clean updates."""
        pass

    @abstractmethod
    async def _delete_all(self) -> bool:
        """Delete all artifacts."""
        pass

    @abstractmethod
    async def _delete_by_id(self, artifact_id: UUID) -> bool:
        """Delete single artifact by ID."""
        pass

    @abstractmethod
    async def _delete_by_filters(
        self, tags: Optional[List[str]], filters: Optional[Dict[str, Any]]
    ) -> bool:
        """Delete artifacts by filters."""
        pass

    # Optional overrides for storage-specific optimizations

    def _has_search(self, search_type: SearchType) -> bool:
        """Override if backend has native search capabilities."""
        return False

    async def _search(
        self,
        query: str,
        search_type: SearchType,
        limit: int,
        threshold: float,
        tags: Optional[List[str]],
        memory_type: Optional[MemoryType],
        filters: Optional[Dict[str, Any]],
        **kwargs,
    ) -> List[Memory]:
        """Override for native search implementation."""
        raise NotImplementedError("Native search not implemented")

    async def _embed(self, content: str) -> Optional[List[float]]:
        """Override for efficient embedding generation."""
        return None


def setup_memory(memory):
    """Setup memory backend with auto-detection."""
    if memory is False:
        return None
    if memory is not None:
        return memory
    
    # Auto-detect default singleton
    global _memory_instance
    if _memory_instance is None:
        from cogency.memory.backends.filesystem import FileBackend
        _memory_instance = FileBackend(".cogency/memory")
    return _memory_instance
