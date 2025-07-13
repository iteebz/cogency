"""Filesystem-based memory implementation for Cogency agents."""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from uuid import UUID

from .base import BaseMemory, MemoryArtifact, MemoryType
from .filters import filter_artifacts


class FSMemory(BaseMemory):
    """Filesystem-based memory backend.
    
    Stores memory artifacts as JSON files in a directory structure.
    Uses simple text matching for recall operations.
    """

    def __init__(self, memory_dir: str = ".cogency_memory"):
        """Initialize filesystem memory.
        
        Args:
            memory_dir: Directory to store memory files
        """
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)

    async def memorize(
        self, 
        content: str,
        memory_type: MemoryType = MemoryType.FACT,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timeout_seconds: float = 10.0
    ) -> MemoryArtifact:
        """Store content as JSON file."""
        artifact = MemoryArtifact(
            content=content,
            memory_type=memory_type,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        # Save as JSON file with UUID as filename
        file_path = self.memory_dir / f"{artifact.id}.json"
        artifact_data = {
            "id": str(artifact.id),
            "content": artifact.content,
            "memory_type": artifact.memory_type.value,
            "tags": artifact.tags,
            "metadata": artifact.metadata,
            "created_at": artifact.created_at.isoformat()
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(artifact_data, f, indent=2, ensure_ascii=False)
        
        return artifact

    async def recall(
        self, 
        query: str,
        limit: Optional[int] = None,
        tags: Optional[List[str]] = None,
        memory_type: Optional[MemoryType] = None,
        since: Optional[str] = None,
        **kwargs
    ) -> List[MemoryArtifact]:
        """Search artifacts using simple text matching."""
        artifacts = []
        query_lower = query.lower()
        
        # Load all artifacts from filesystem
        for file_path in self.memory_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Simple text matching in content and tags
                content_match = query_lower in data["content"].lower()
                tag_match = any(query_lower in tag.lower() for tag in data["tags"])
                
                # Apply common filters
                if not filter_artifacts(data, memory_type, tags, since):
                    continue
                
                if content_match or tag_match:
                    artifact = MemoryArtifact(
                        content=data["content"],
                        memory_type=MemoryType(data.get("memory_type", MemoryType.FACT.value)),
                        id=UUID(data["id"]),
                        tags=data["tags"],
                        metadata=data["metadata"]
                    )
                    # Parse datetime
                    artifact.created_at = datetime.fromisoformat(data["created_at"])
                    artifacts.append(artifact)
                    
            except (json.JSONDecodeError, KeyError, ValueError):
                # Skip corrupted files
                continue
        
        # Sort by recency (most recent first)
        artifacts.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply limit
        if limit:
            artifacts = artifacts[:limit]
        
        return artifacts

    async def forget(self, artifact_id: UUID) -> bool:
        """Remove artifact file."""
        file_path = self.memory_dir / f"{artifact_id}.json"
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    async def clear(self) -> None:
        """Remove all artifact files."""
        for file_path in self.memory_dir.glob("*.json"):
            file_path.unlink()