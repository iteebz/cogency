"""Base memory abstraction for Cogency agents."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, UTC, timedelta
from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import uuid4, UUID


class MemoryType(Enum):
    """Types of memory for different agent use cases."""
    MESSAGE = "message"    # Fine-grained message recall
    SUMMARY = "summary"    # Thread/block summaries
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

    def __str__(self) -> str:
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"MemoryArtifact(id={self.id}, content='{preview}', tags={self.tags})"


class BaseMemory(ABC):
    """Abstract base class for memory backends used by Cogency agents.
    
    Provides recall and memorize operations that can be executed in parallel
    during ReAct reasoning loops.
    """

    @abstractmethod
    async def memorize(
        self, 
        content: str,
        memory_type: MemoryType = MemoryType.FACT,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MemoryArtifact:
        """Store new content in memory.
        
        Args:
            content: The text content to store
            memory_type: Type of memory for semantic organization
            tags: Optional list of tags for categorization
            metadata: Optional metadata dictionary
            
        Returns:
            The created MemoryArtifact
        """
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
        """Retrieve relevant content from memory.
        
        Args:
            query: Search query to match against content
            limit: Maximum number of results to return
            tags: Optional tags to filter by
            memory_type: Optional memory type to filter by
            since: Optional ISO datetime string to filter by recency
            **kwargs: Backend-specific parameters
            
        Returns:
            List of matching MemoryArtifacts, ordered by relevance/recency
        """
        pass

    async def forget(self, artifact_id: UUID) -> bool:
        """Remove an artifact from memory.
        
        Args:
            artifact_id: ID of the artifact to remove
            
        Returns:
            True if artifact was removed, False if not found
        """
        raise NotImplementedError("forget() not implemented for this memory backend")

    async def clear(self) -> None:
        """Clear all artifacts from memory.
        
        This is mainly for testing and should be used with caution.
        """
        raise NotImplementedError("clear() not implemented for this memory backend")

    # Utility methods for common patterns
    async def recall_by_type(
        self, 
        memory_type: MemoryType, 
        limit: Optional[int] = None,
        **kwargs
    ) -> List[MemoryArtifact]:
        """Convenience method to recall by memory type only."""
        return await self.recall("", memory_type=memory_type, limit=limit, **kwargs)
    
    async def recall_recent(
        self, 
        hours: int = 24,
        memory_type: Optional[MemoryType] = None,
        limit: Optional[int] = None,
        **kwargs
    ) -> List[MemoryArtifact]:
        """Convenience method to recall recent memories."""
        since = (datetime.now(UTC) - timedelta(hours=hours)).isoformat()
        return await self.recall("", since=since, memory_type=memory_type, limit=limit, **kwargs)