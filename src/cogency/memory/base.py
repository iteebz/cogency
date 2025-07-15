"""Base memory abstraction for Cogency agents."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import uuid4, UUID


class MemoryType(Enum):
    """Types of memory for different agent use cases."""
    FACT = "fact"         # Semantic knowledge units
    CONTEXT = "context"   # Working memory/history


@dataclass
class MemoryArtifact:
    """A memory artifact with content and metadata."""
    content: str
    memory_type: MemoryType = MemoryType.FACT
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    
    # Phase 2: Enhanced relevance scoring
    relevance_score: float = 0.0
    confidence_score: float = 1.0
    access_count: int = 0
    last_accessed: datetime = field(default_factory=lambda: datetime.now(UTC))
    
    def decay_score(self) -> float:
        """Calculate decay based on recency and confidence."""
        now = datetime.now(UTC)
        days_since_created = (now - self.created_at).days
        days_since_accessed = (now - self.last_accessed).days
        
        # Decay formula: confidence * recency_factor * access_boost
        recency_factor = max(0.1, 1.0 - (days_since_created * 0.05))
        access_boost = min(2.0, 1.0 + (self.access_count * 0.1))
        staleness_penalty = max(0.5, 1.0 - (days_since_accessed * 0.02))
        
        return self.confidence_score * recency_factor * access_boost * staleness_penalty


class BaseMemory(ABC):
    """Abstract base class for memory backends."""

    @abstractmethod
    async def memorize(
        self, 
        content: str,
        memory_type: MemoryType = MemoryType.FACT,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timeout_seconds: float = 10.0
    ) -> MemoryArtifact:
        """Store new content in memory."""
        pass

    @abstractmethod
    async def recall(
        self, 
        query: str,
        limit: Optional[int] = None,
        tags: Optional[List[str]] = None,
        memory_type: Optional[MemoryType] = None,
        since: Optional[str] = None,
        **kwargs
    ) -> List[MemoryArtifact]:
        """Retrieve relevant content from memory."""
        pass

    async def forget(self, artifact_id: UUID) -> bool:
        """Remove an artifact from memory."""
        raise NotImplementedError("forget() not implemented for this memory backend")

    async def clear(self) -> None:
        """Clear all artifacts from memory."""
        raise NotImplementedError("clear() not implemented for this memory backend")
    
    async def inspect(self) -> Dict[str, Any]:
        """Dev tooling - inspect memory state."""
        all_artifacts = await self.recall("", limit=1000)
        recent = all_artifacts[:3]
        
        base_stats = {
            "count": len(all_artifacts),
            "recent": [{
                "content": a.content[:50] + "..." if len(a.content) > 50 else a.content,
                "tags": a.tags,
                "created": a.created_at.strftime("%Y-%m-%d %H:%M:%S")
            } for a in recent]
        }
        
        # Add backend-specific stats if available
        if hasattr(self, '_get_fs_stats'):
            base_stats.update(self._get_fs_stats())
        
        return base_stats