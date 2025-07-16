"""Core memory interfaces and types."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import uuid4, UUID


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
class MemoryArtifact:
    """A memory artifact with content and metadata."""
    content: str
    memory_type: MemoryType = MemoryType.FACT
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    relevance_score: float = 0.0
    confidence_score: float = 1.0
    access_count: int = 0
    last_accessed: datetime = field(default_factory=lambda: datetime.now(UTC))
    
    def decay_score(self) -> float:
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

    def __init__(self, embedding_provider=None):
        self.embedding_provider = embedding_provider

    @abstractmethod
    async def memorize(
        self, 
        content: str,
        memory_type: MemoryType = MemoryType.FACT,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> MemoryArtifact:
        """Store new content in memory."""
        pass

    @abstractmethod
    async def recall(
        self, 
        query: str,
        search_type: SearchType = SearchType.AUTO,
        limit: int = 10,
        threshold: float = 0.7,
        tags: Optional[List[str]] = None,
        memory_type: Optional[MemoryType] = None,
        **kwargs
    ) -> List[MemoryArtifact]:
        """Retrieve relevant content from memory."""
        pass

    async def forget(self, artifact_id: UUID) -> bool:
        """Remove an artifact from memory."""
        raise NotImplementedError()

    async def clear(self) -> None:
        """Clear all artifacts from memory."""
        raise NotImplementedError()


class Memory:
    """Magical memory interface that auto-configures backends."""
    
    @staticmethod
    def create(backend_name: str = "filesystem", **config) -> MemoryBackend:
        """Auto-magical backend creation."""
        from .backends import get_backend
        backend_class = get_backend(backend_name)
        return backend_class(**config)
    
    @staticmethod
    def list_backends() -> List[str]:
        """List available backend names."""
        from .backends import list_backends
        return list_backends()