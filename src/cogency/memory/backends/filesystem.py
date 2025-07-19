"""Filesystem storage implementation."""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from uuid import UUID

from ..core import MemoryBackend, MemoryArtifact, MemoryType, SearchType
from ..search import search_artifacts

logger = logging.getLogger(__name__)


class FilesystemBackend(MemoryBackend):
    """Filesystem storage implementation."""
    
    def __init__(self, memory_dir: str = ".cogency/memory", embedding_provider=None):
        super().__init__(embedding_provider)
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
    
    async def memorize(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.FACT,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> MemoryArtifact:
        artifact = MemoryArtifact(
            content=content,
            memory_type=memory_type,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        embedding = None
        if self.embedding_provider:
            try:
                embedding = await self.embedding_provider.embed_text(content)
            except Exception as e:
                logger.warning(f"Failed to generate embedding for content: {e}")
                # Continue without embedding - not a critical failure
        
        user_id = kwargs.get('user_id', 'default')
        user_dir = self.memory_dir / user_id
        user_dir.mkdir(exist_ok=True)
        
        data = {
            "id": str(artifact.id),
            "content": artifact.content,
            "memory_type": artifact.memory_type.value,
            "tags": artifact.tags,
            "metadata": artifact.metadata,
            "created_at": artifact.created_at.isoformat(),
            "confidence_score": artifact.confidence_score,
            "access_count": artifact.access_count,
            "last_accessed": artifact.last_accessed.isoformat(),
            "embedding": embedding
        }
        
        try:
            with open(user_dir / f"{artifact.id}.json", 'w') as f:
                json.dump(data, f, indent=2)
        except (OSError, IOError) as e:
            logger.error(f"Failed to save memory artifact {artifact.id}: {e}")
            raise RuntimeError(f"Failed to save memory: {e}") from e
        
        return artifact
    
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
        user_id = kwargs.get('user_id', 'default')
        user_dir = self.memory_dir / user_id
        
        artifacts = []
        if user_dir.exists():
            for file_path in user_dir.glob("*.json"):
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    artifact = self._data_to_artifact(data)
                    
                    # Apply filters
                    if memory_type and artifact.memory_type != memory_type:
                        continue
                    if tags and not any(tag in artifact.tags for tag in tags):
                        continue
                    
                    artifacts.append(artifact)
                except (OSError, IOError, json.JSONDecodeError, KeyError, ValueError) as e:
                    logger.warning(f"Skipping corrupted memory file {file_path}: {e}")
                    continue
        
        def get_embedding(artifact_id: UUID) -> Optional[List[float]]:
            try:
                with open(user_dir / f"{artifact_id}.json", 'r') as f:
                    data = json.load(f)
                return data.get("embedding")
            except (OSError, IOError, json.JSONDecodeError) as e:
                logger.debug(f"Could not load embedding for {artifact_id}: {e}")
                return None
        
        return await search_artifacts(
            query, artifacts, search_type, threshold,
            self.embedding_provider, get_embedding
        )
    
    
    async def forget(self, artifact_id: UUID, user_id: str = "default") -> bool:
        """Delete a specific memory artifact."""
        try:
            file_path = self.memory_dir / user_id / f"{artifact_id}.json"
            file_path.unlink()
            logger.debug(f"Deleted memory artifact {artifact_id} for user {user_id}")
            return True
        except FileNotFoundError:
            logger.warning(f"Memory artifact {artifact_id} not found for user {user_id}")
            return False
        except (OSError, IOError) as e:
            logger.error(f"Failed to delete memory artifact {artifact_id}: {e}")
            return False
    
    async def clear(self, user_id: Optional[str] = None) -> None:
        """Clear memories for a specific user or all users."""
        try:
            if user_id:
                # Clear specific user's memories
                user_dir = self.memory_dir / user_id
                if user_dir.exists():
                    for file_path in user_dir.glob("*.json"):
                        file_path.unlink()
                    logger.info(f"Cleared memories for user {user_id}")
            else:
                # Clear all memories
                for file_path in self.memory_dir.rglob("*.json"):
                    file_path.unlink()
                logger.info("Cleared all memories")
        except (OSError, IOError) as e:
            logger.error(f"Failed to clear memories: {e}")
            raise RuntimeError(f"Failed to clear memories: {e}") from e
    
    def _data_to_artifact(self, data: Dict) -> MemoryArtifact:
        artifact = MemoryArtifact(
            id=UUID(data["id"]),
            content=data["content"],
            memory_type=MemoryType(data["memory_type"]),
            tags=data["tags"],
            metadata=data["metadata"],
            confidence_score=data.get("confidence_score", 1.0),
            access_count=data.get("access_count", 0)
        )
        artifact.created_at = datetime.fromisoformat(data["created_at"])
        artifact.last_accessed = datetime.fromisoformat(data.get("last_accessed", data["created_at"]))
        return artifact