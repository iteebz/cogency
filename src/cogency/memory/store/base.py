"""Memory store interface and shared implementation."""

from typing import Any, Dict, List, Optional
from uuid import UUID

from resilient_result import Result, Retry, resilient

from cogency.memory.search import search
from cogency.memory.types import Memory, MemoryType, SearchType

# Singleton instance for default memory store
_memory_instance = None


class Store:
    """Memory store with extensible backend implementations."""

    def __init__(self, embedder=None):
        self.embedder = embedder

    @resilient(retry=Retry.api())
    async def create(
        self,
        content: str,
        type: MemoryType = MemoryType.FACT,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Result:
        """CREATE - Standard artifact creation with storage delegation."""
        await self._ready()

        artifact = Memory(
            content=content,
            type=type,
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
        id: UUID = None,
        search_type: SearchType = SearchType.AUTO,
        limit: int = 10,
        threshold: float = 0.7,
        tags: Optional[List[str]] = None,
        type: Optional[MemoryType] = None,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Result:
        """READ - Unified retrieval with assertive parameter validation."""
        await self._ready()

        # Count specified parameters for validation
        specified_params = sum(
            [query is not None, id is not None, bool(tags), bool(filters), type is not None]
        )

        # Handle ID lookup
        if id:
            if specified_params > 1:
                raise ValueError("Cannot combine id lookup with other search criteria")
            results = await self._read(id=id, **kwargs)
            return Result.ok(results)

        # Handle query search
        if query:
            # Query-based search with storage-specific optimizations
            if self._has_search(search_type):
                results = await self._search(
                    query,
                    search_type,
                    limit,
                    threshold,
                    tags,
                    type,
                    filters,
                    **kwargs,
                )
                return Result.ok(results)

            # Fallback to search module
            artifacts = await self._read(type=type, tags=tags, filters=filters, **kwargs)

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

        # Handle filtering (no query, no id)
        if specified_params == 0:
            raise ValueError("Must specify search criteria: query, id, tags, type, or filters")

        results = await self._read(type=type, tags=tags, filters=filters, **kwargs)
        return Result.ok(results)

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
        all: bool = False,
        **kwargs,
    ) -> Result:
        """DELETE - Unified deletion with assertive parameter validation."""
        await self._ready()

        # Count specified parameters for validation
        specified_params = sum([artifact_id is not None, bool(tags), bool(filters), all])

        # Assertive validation - exactly one deletion criteria must be specified
        if specified_params == 0:
            raise ValueError(
                "Must specify deletion criteria: artifact_id, tags, filters, or all=True"
            )

        if specified_params > 1:
            raise ValueError("Cannot specify multiple deletion criteria simultaneously")

        success = await self._delete(id=artifact_id, tags=tags, filters=filters, all=all, **kwargs)
        return Result.ok(success)

    # Storage primitives - implement these in subclasses

    async def _ready(self) -> None:
        """Ensure store is initialized and ready."""
        raise NotImplementedError

    async def _store(self, artifact: Memory, embedding: Optional[List[float]], **kwargs) -> None:
        """Store artifact with embedding."""
        raise NotImplementedError

    async def _read(
        self,
        id: UUID = None,
        type: Optional[MemoryType] = None,
        tags: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> List[Memory]:
        """Read artifacts - handles both ID lookup and filtering."""
        raise NotImplementedError

    async def _update(self, artifact_id: UUID, updates: Dict[str, Any]) -> bool:
        """Update artifact with clean updates."""
        raise NotImplementedError

    async def _delete(
        self,
        id: UUID = None,
        tags: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        all: bool = False,
        **kwargs,
    ) -> bool:
        """Delete artifacts - handles all deletion scenarios."""
        raise NotImplementedError

    # Optional overrides for storage-specific optimizations

    def _has_search(self, search_type: SearchType) -> bool:
        """Override if store has native search capabilities."""
        return False

    async def _search(
        self,
        query: str,
        search_type: SearchType,
        limit: int,
        threshold: float,
        tags: Optional[List[str]],
        type: Optional[MemoryType],
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
        from cogency.memory import Filesystem

        _memory_instance = Filesystem(".cogency/memory")
    return _memory_instance
