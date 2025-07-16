"""Base memory abstraction for Cogency agents."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import uuid4, UUID


class MemoryType(Enum):
    """Types of memory for different agent use cases."""
    FACT = "fact"             # Static semantic knowledge - "Paris is in France"
    EPISODIC = "episodic"     # Personal experiences, conversations - "User asked about ML on Tuesday"
    EXPERIENCE = "experience" # Learned patterns, procedural knowledge - "When users ask X, do Y"
    CONTEXT = "context"       # Working memory, recent conversation history


class SearchType(Enum):
    """Search methods for memory recall."""
    AUTO = "auto"         # Backend chooses best method
    SEMANTIC = "semantic" # Vector similarity search
    TEXT = "text"         # Keyword/regex matching
    HYBRID = "hybrid"     # Combined semantic + text
    TAGS = "tags"         # Tag-only search (query ignored)


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

    def __init__(self, embedding_provider=None):
        """Initialize memory backend with optional embedding provider."""
        self.embedding_provider = embedding_provider

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
        search_type: SearchType = SearchType.AUTO,
        limit: int = 10,
        threshold: float = 0.7,
        tags: Optional[List[str]] = None,
        memory_type: Optional[MemoryType] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        since: Optional[str] = None,
        **kwargs
    ) -> List[MemoryArtifact]:
        """Retrieve relevant content from memory using unified search interface."""
        pass

    async def forget(self, artifact_id: UUID) -> bool:
        """Remove an artifact from memory."""
        raise NotImplementedError("forget() not implemented for this memory backend")

    async def clear(self) -> None:
        """Clear all artifacts from memory."""
        raise NotImplementedError("clear() not implemented for this memory backend")
    
    async def recall_by_tags(self, tags: List[str], limit: int = 10, **kwargs) -> List[MemoryArtifact]:
        """Convenience method for tag-only search."""
        return await self.recall(
            query="",  # Ignored for tag search
            search_type=SearchType.TAGS,
            tags=tags,
            limit=limit,
            **kwargs
        )
    
    async def recall_smart(self, query: str, tags: Optional[List[str]] = None, **kwargs) -> List[MemoryArtifact]:
        """Smart recall that combines query + tag filtering automatically."""
        if not query and tags:
            # Tag-only search
            return await self.recall_by_tags(tags, **kwargs)
        elif query and tags:
            # Hybrid search with tag filtering
            return await self.recall(
                query=query,
                search_type=SearchType.HYBRID,
                tags=tags,
                **kwargs
            )
        else:
            # Regular auto search
            return await self.recall(query=query, **kwargs)
    
    async def get_all_tags(self) -> List[str]:
        """Get all unique tags in the memory store."""
        all_artifacts = await self.recall("", limit=1000)
        all_tags = set()
        for artifact in all_artifacts:
            all_tags.update(artifact.tags)
        return sorted(list(all_tags))

    async def inspect(self) -> Dict[str, Any]:
        """Dev tooling - inspect memory state."""
        all_artifacts = await self.recall("", limit=1000)
        recent = all_artifacts[:3]
        
        # Tag statistics
        all_tags = set()
        tag_counts = {}
        for artifact in all_artifacts:
            for tag in artifact.tags:
                all_tags.add(tag)
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        base_stats = {
            "count": len(all_artifacts),
            "unique_tags": len(all_tags),
            "top_tags": sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            "recent": [{
                "content": a.content[:50] + "..." if len(a.content) > 50 else a.content,
                "tags": a.tags,
                "memory_type": a.memory_type.value,
                "created": a.created_at.strftime("%Y-%m-%d %H:%M:%S")
            } for a in recent]
        }
        
        # Add backend-specific stats if available
        if hasattr(self, '_get_fs_stats'):
            base_stats.update(self._get_fs_stats())
        
        return base_stats