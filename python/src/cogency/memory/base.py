"""Base memory abstraction for Cogency agents."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import List, Optional, Dict, Any
from uuid import uuid4, UUID


@dataclass
class MemoryArtifact:
    """A memory artifact with content and metadata."""
    content: str
    id: UUID = field(default_factory=uuid4)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
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
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MemoryArtifact:
        """Store new content in memory.
        
        Args:
            content: The text content to store
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
        tags: Optional[List[str]] = None
    ) -> List[MemoryArtifact]:
        """Retrieve relevant content from memory.
        
        Args:
            query: Search query to match against content
            limit: Maximum number of results to return
            tags: Optional tags to filter by
            
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