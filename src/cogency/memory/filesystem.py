"""Filesystem-based memory implementation for Cogency agents."""
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID

from .base import BaseMemory, MemoryArtifact, MemoryType
from .filters import filter_artifacts


class FSMemory(BaseMemory):
    """Filesystem-based memory backend.
    
    Stores memory artifacts as JSON files in a directory structure.
    Uses simple text matching for recall operations.
    """

    def __init__(self, memory_dir: str = ".memory"):
        """Initialize filesystem memory.
        
        Args:
            memory_dir: Directory to store memory files
        """
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)
    
    def should_store(self, text: str) -> Tuple[bool, str]:
        """Smart auto-storage heuristics - NO BULLSHIT."""
        triggers = [
            (r"\bi am\b", "personal"),
            (r"\bi have\b", "personal"), 
            (r"\bi work\b", "work"),
            (r"\bi like\b", "preferences"),
            (r"\bmy name is\b", "personal"),
            (r"\badhd\b", "personal"),
            (r"\bsoftware engineer\b", "work"),
            (r"\bdeveloper\b", "work")
        ]
        
        text_lower = text.lower()
        for pattern, category in triggers:
            if re.search(pattern, text_lower):
                return True, category
        return False, ""

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
                
                # Better text matching - split query into words
                content_lower = data["content"].lower()
                query_words = query_lower.split()
                
                # Match if any query word appears in content or tags
                content_match = any(word in content_lower for word in query_words)
                tag_match = any(word in tag.lower() for tag in data["tags"] for word in query_words)
                
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
    
    def _get_fs_stats(self) -> Dict[str, Any]:
        """Get filesystem-specific stats."""
        files = list(self.memory_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in files)
        return {
            "count": len(files),
            "total_size_kb": round(total_size / 1024, 1),
            "directory": str(self.memory_dir)
        }