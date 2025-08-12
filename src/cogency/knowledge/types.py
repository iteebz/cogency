"""Knowledge artifact types - structured knowledge representation."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class KnowledgeArtifact:
    """Structured knowledge extracted from conversations."""

    topic: str
    content: str
    confidence: float = 0.8
    context: str = ""
    user_id: str = "default"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    source_conversations: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "topic": self.topic,
            "content": self.content,
            "confidence": self.confidence,
            "context": self.context,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "source_conversations": self.source_conversations,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "KnowledgeArtifact":
        """Create from dictionary."""
        data = data.copy()
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if isinstance(data.get("updated_at"), str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return cls(**data)
