"""Filesystem storage implementation."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from cogency.memory.store.base import Store
from cogency.memory.types import Memory, MemoryType

logger = logging.getLogger(__name__)


class Filesystem(Store):
    """Filesystem storage implementation."""

    def __init__(self, memory_dir: str = ".cogency/memory", embedder=None):
        super().__init__(embedder)
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)

    def _find_artifact_file(self, artifact_id: UUID) -> Optional[Path]:
        """Find artifact file across all user directories."""
        for user_dir in self.memory_dir.iterdir():
            if not user_dir.is_dir():
                continue
            file_path = user_dir / f"{artifact_id}.json"
            if file_path.exists():
                return file_path
        return None

    async def _ready(self) -> None:
        """Filesystem is always ready - directory created in __init__."""
        pass

    async def _store(self, artifact: Memory, embedding: Optional[List[float]], **kwargs) -> None:
        """Store artifact to filesystem."""
        user_id = kwargs.get("user_id", "default")
        user_dir = self.memory_dir / user_id
        user_dir.mkdir(exist_ok=True)

        data = artifact.to_dict()
        data["embedding"] = embedding

        try:
            with open(user_dir / f"{artifact.id}.json", "w") as f:
                json.dump(data, f, indent=2)
        except OSError as e:
            logger.error(f"Failed to save memory artifact {artifact.id}: {e}")
            raise RuntimeError(f"Failed to save memory: {e}") from e

    async def _read(
        self,
        id: UUID = None,
        type: Optional[MemoryType] = None,
        tags: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> List[Memory]:
        """Read artifacts - handles both ID lookup and filtering."""
        # Handle ID lookup
        if id:
            file_path = self._find_artifact_file(id)
            if not file_path:
                return []

            try:
                with open(file_path) as f:
                    data = json.load(f)
                return [Memory.from_dict(data)]
            except (OSError, json.JSONDecodeError, KeyError, ValueError):
                return []

        # Handle filtering
        user_id = kwargs.get("user_id", "default")
        user_dir = self.memory_dir / user_id

        artifacts = []
        if user_dir.exists():
            for file_path in user_dir.glob("*.json"):
                try:
                    with open(file_path) as f:
                        data = json.load(f)

                    artifact = Memory.from_dict(data)

                    # Apply filters
                    if type and artifact.type != type:
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
                except (OSError, json.JSONDecodeError, KeyError, ValueError) as e:
                    logger.warning(f"Skipping corrupted memory file {file_path}: {e}")
                    continue

        return artifacts

    async def _update(self, artifact_id: UUID, updates: Dict[str, Any]) -> bool:
        """Update artifact with clean updates."""
        file_path = self._find_artifact_file(artifact_id)
        if not file_path:
            return False

        try:
            with open(file_path) as f:
                data = json.load(f)

            # Apply updates
            for key, value in updates.items():
                if (
                    key == "tags"
                    and isinstance(value, list)
                    or key == "metadata"
                    and isinstance(value, dict)
                    or key in ["access_count", "confidence_score", "relevance_score"]
                ):
                    data[key] = value
                elif key in ["last_accessed", "created_at"]:
                    data[key] = value.isoformat() if hasattr(value, "isoformat") else value
                else:
                    data[key] = value

            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)

            return True
        except (OSError, json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to update artifact {artifact_id}: {e}")
            return False

    async def _delete(
        self,
        id: UUID = None,
        tags: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        all: bool = False,
        **kwargs,
    ) -> bool:
        """Delete artifacts - handles all deletion scenarios."""
        try:
            # Delete all artifacts
            if all:
                for user_dir in self.memory_dir.iterdir():
                    if user_dir.is_dir():
                        for file_path in user_dir.glob("*.json"):
                            file_path.unlink()
                return True

            # Delete by ID
            if id:
                file_path = self._find_artifact_file(id)
                if not file_path:
                    return False
                file_path.unlink()
                return True

            # Delete by filters
            if tags or filters:
                user_id = kwargs.get(
                    "user_id", filters.get("user_id", "default") if filters else "default"
                )
                artifacts_to_delete = await self._read(tags=tags, filters=filters, user_id=user_id)

                user_dir = self.memory_dir / user_id
                for artifact in artifacts_to_delete:
                    file_path = user_dir / f"{artifact.id}.json"
                    file_path.unlink()
                return True

            return False

        except (OSError, FileNotFoundError) as e:
            logger.error(f"Failed to delete artifacts: {e}")
            return False

    async def _embed(self, artifact_id: UUID) -> Optional[List[float]]:
        """Get embedding for search operations."""
        file_path = self._find_artifact_file(artifact_id)
        if not file_path:
            return None

        try:
            with open(file_path) as f:
                data = json.load(f)
            return data.get("embedding")
        except (OSError, json.JSONDecodeError):
            return None
