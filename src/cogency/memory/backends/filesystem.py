"""Filesystem storage implementation."""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from uuid import UUID

from .base import BaseCRUDBackend
from ..core import MemoryArtifact, MemoryType

logger = logging.getLogger(__name__)


class FilesystemBackend(BaseCRUDBackend):
    """Filesystem storage implementation."""
    
    def __init__(self, memory_dir: str = ".cogency/memory", embedding_provider=None):
        super().__init__(embedding_provider)
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
    
    async def _ensure_ready(self) -> None:
        """Filesystem is always ready - directory created in __init__."""
        pass
    
    async def _store_artifact(self, artifact: MemoryArtifact, embedding: Optional[List[float]], **kwargs) -> None:
        """Store artifact to filesystem."""
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
    
    async def _read_by_id(self, artifact_id: UUID) -> List[MemoryArtifact]:
        """Read single artifact by ID."""
        # Check all user directories for the artifact
        for user_dir in self.memory_dir.iterdir():
            if not user_dir.is_dir():
                continue
            try:
                file_path = user_dir / f"{artifact_id}.json"
                with open(file_path, 'r') as f:
                    data = json.load(f)
                return [self._data_to_artifact(data)]
            except (OSError, IOError, json.JSONDecodeError, KeyError, ValueError):
                continue
        return []
    
    async def _read_filtered(
        self,
        memory_type: Optional[MemoryType] = None,
        tags: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[MemoryArtifact]:
        """Read filtered artifacts."""
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
                    if filters:
                        skip = False
                        for key, value in filters.items():
                            if not hasattr(artifact, key) or getattr(artifact, key) != value:
                                skip = True
                                break
                        if skip:
                            continue
                    
                    artifacts.append(artifact)
                except (OSError, IOError, json.JSONDecodeError, KeyError, ValueError) as e:
                    logger.warning(f"Skipping corrupted memory file {file_path}: {e}")
                    continue
        
        return artifacts
    
    async def _update_artifact(self, artifact_id: UUID, updates: Dict[str, Any]) -> bool:
        """Update artifact with clean updates."""
        # Find artifact file across user directories
        for user_dir in self.memory_dir.iterdir():
            if not user_dir.is_dir():
                continue
            file_path = user_dir / f"{artifact_id}.json"
            if not file_path.exists():
                continue
                
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # Apply updates
                for key, value in updates.items():
                    if key == 'tags' and isinstance(value, list):
                        data[key] = value
                    elif key == 'metadata' and isinstance(value, dict):
                        data[key] = value
                    elif key in ['access_count', 'confidence_score', 'relevance_score']:
                        data[key] = value
                    elif key in ['last_accessed', 'created_at']:
                        data[key] = value.isoformat() if hasattr(value, 'isoformat') else value
                    else:
                        data[key] = value
                
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=2)
                
                return True
            except (OSError, IOError, json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to update artifact {artifact_id}: {e}")
                return False
        
        return False
    
    async def _delete_all(self) -> bool:
        """Delete all artifacts."""
        try:
            for user_dir in self.memory_dir.iterdir():
                if user_dir.is_dir():
                    for file_path in user_dir.glob("*.json"):
                        file_path.unlink()
            return True
        except OSError:
            return False
    
    async def _delete_by_id(self, artifact_id: UUID) -> bool:
        """Delete single artifact by ID."""
        for user_dir in self.memory_dir.iterdir():
            if not user_dir.is_dir():
                continue
            try:
                file_path = user_dir / f"{artifact_id}.json"
                file_path.unlink()
                return True
            except FileNotFoundError:
                continue
        return False
    
    async def _delete_by_filters(self, tags: Optional[List[str]], filters: Optional[Dict[str, Any]]) -> bool:
        """Delete artifacts by filters."""
        user_id = filters.get('user_id', 'default') if filters else 'default'
        artifacts_to_delete = await self._read_filtered(tags=tags, filters=filters, user_id=user_id)
        
        try:
            user_dir = self.memory_dir / user_id
            for artifact in artifacts_to_delete:
                file_path = user_dir / f"{artifact.id}.json"
                file_path.unlink()
            return True
        except (OSError, FileNotFoundError):
            return False
    
    async def _get_embedding_for_search(self, artifact_id: UUID) -> Optional[List[float]]:
        """Get embedding for search operations."""
        for user_dir in self.memory_dir.iterdir():
            if not user_dir.is_dir():
                continue
            try:
                with open(user_dir / f"{artifact_id}.json", 'r') as f:
                    data = json.load(f)
                return data.get("embedding")
            except (OSError, IOError, json.JSONDecodeError):
                continue
        return None
    
    def _data_to_artifact(self, data: Dict) -> MemoryArtifact:
        """Convert JSON data to MemoryArtifact."""
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