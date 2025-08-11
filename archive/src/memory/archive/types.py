"""Archive memory types - clean dataclasses."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TopicArtifact:
    """Topic artifact with metadata and content."""

    topic: str
    content: str
    created: str = field(default_factory=lambda: datetime.now().isoformat())
    updated: str = field(default_factory=lambda: datetime.now().isoformat())
    source_conversations: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        """Initialize from metadata if provided."""
        if self.metadata:
            self.created = self.metadata.get("created", self.created)
            self.updated = self.metadata.get("updated", self.updated)
            self.source_conversations = self.metadata.get(
                "source_conversations", self.source_conversations
            )
