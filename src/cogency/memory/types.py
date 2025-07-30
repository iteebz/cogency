"""Core memory interfaces and types."""

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Dict, List
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
    type: MemoryType = MemoryType.FACT
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    relevance_score: float = 0.0
    confidence: float = DEFAULT_CONFIDENCE_SCORE
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

        return self.confidence * recency_factor * access_boost * staleness_penalty

    def to_dict(self) -> Dict[str, Any]:
        """Convert Memory to dictionary for serialization."""
        return {
            "id": str(self.id),
            "content": self.content,
            "type": self.type.value,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "confidence": self.confidence,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Memory":
        """Create Memory from dictionary."""
        memory = cls(
            id=UUID(data["id"]),
            content=data["content"],
            type=MemoryType(data.get("type", data.get("memory_type", "fact"))),  # backwards compat
            tags=data["tags"],
            metadata=data["metadata"],
            confidence=data.get(
                "confidence", data.get("confidence_score", DEFAULT_CONFIDENCE_SCORE)
            ),  # backwards compat
            access_count=data.get("access_count", 0),
        )
        memory.created_at = datetime.fromisoformat(data["created_at"])
        memory.last_accessed = datetime.fromisoformat(data.get("last_accessed", data["created_at"]))
        return memory
