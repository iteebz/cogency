"""Core memory interfaces and types."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)

DEFAULT_RELEVANCE_THRESHOLD = 0.7
DEFAULT_CONFIDENCE_SCORE = 1.0


class MemoryType(Enum):
    """Types of memory for different agent use cases."""

    FACT = "fact"
    EPISODIC = "episodic"
    EXPERIENCE = "experience"
    CONTEXT = "context"


class SearchType(Enum):
    """Search methods for memory recall."""

    AUTO = "auto"
    SEMANTIC = "semantic"
    TEXT = "text"
    HYBRID = "hybrid"
    TAGS = "tags"


@dataclass
class Memory:
    """A memory artifact with content and metadata."""

    content: str
    memory_type: MemoryType = MemoryType.FACT
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    relevance_score: float = 0.0
    confidence_score: float = DEFAULT_CONFIDENCE_SCORE
    access_count: int = 0
    last_accessed: datetime = field(default_factory=lambda: datetime.now(UTC))

    def decay(self) -> float:
        """Calculate decay based on recency and confidence."""
        now = datetime.now(UTC)
        days_since_created = (now - self.created_at).days
        days_since_accessed = (now - self.last_accessed).days

        recency_factor = max(0.1, 1.0 - (days_since_created * 0.05))
        access_boost = min(2.0, 1.0 + (self.access_count * 0.1))
        staleness_penalty = max(0.5, 1.0 - (days_since_accessed * 0.02))

        return self.confidence_score * recency_factor * access_boost * staleness_penalty


class MemoryBackend(ABC):
    """Abstract base class for memory backends."""

    def __init__(self, embedder=None):
        self.embedder = embedder

    async def _embed(self, content: str) -> Optional[List[float]]:
        """Safely generate embedding with error handling."""
        if not self.embedder:
            return None
        try:
            return await self.embedder.embed_text(content)
        except Exception as e:
            logger.error(f"Context: {e}")
            return None

    def _operate(self, operation_func, *args, **kwargs) -> bool:
        """Safely execute operation, return True/False."""
        try:
            operation_func(*args, **kwargs)
            return True
        except Exception as e:
            logger.error(f"Context: {e}")
            return False

    def _stats(self, stats_func, fallback_backend_name: str, *args, **kwargs) -> Dict[str, Any]:
        """Safely get stats with fallback."""
        try:
            return stats_func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Context: {e}")
            return {"total_memories": 0, "backend": fallback_backend_name}

    @abstractmethod
    async def create(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.FACT,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Memory:
        """CREATE - Store new content in memory."""
        pass

    @abstractmethod
    async def read(
        self,
        query: str = None,
        artifact_id: UUID = None,
        search_type: SearchType = SearchType.AUTO,
        limit: int = 10,
        threshold: float = DEFAULT_RELEVANCE_THRESHOLD,
        tags: Optional[List[str]] = None,
        memory_type: Optional[MemoryType] = None,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> List[Memory]:
        """READ - Flexible retrieval: by query, ID, tags, or filters."""
        pass

    @abstractmethod
    async def update(self, artifact_id: UUID, updates: Dict[str, Any]) -> bool:
        """UPDATE - Modify existing artifact (access_count, metadata, etc.)."""
        pass

    @abstractmethod
    async def delete(
        self,
        artifact_id: UUID = None,
        tags: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        delete_all: bool = False,
    ) -> bool:
        """DELETE - Remove artifacts by ID, tags, filters, or all."""
        pass
