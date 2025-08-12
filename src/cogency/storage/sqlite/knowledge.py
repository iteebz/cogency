"""SQLite knowledge operations - semantic memory persistence."""

from typing import TYPE_CHECKING

import aiosqlite

if TYPE_CHECKING:
    from cogency.knowledge import KnowledgeArtifact

from .base import SQLiteBase
from ...events.orchestration import state_event, extract_knowledge_data, extract_delete_data


class KnowledgeOperations(SQLiteBase):
    """SQLite operations for knowledge artifact persistence."""

    @state_event("knowledge_saved", extract_knowledge_data)
    async def save_knowledge(self, artifact: "KnowledgeArtifact") -> bool:
        """Save knowledge artifact with semantic embedding storage."""
        await self._ensure_schema()

        try:
            from cogency.providers import detect_embed
            from cogency.semantic import add_sqlite_vector

            # Generate embedding for semantic search
            embedder = detect_embed()
            embed_result = await embedder.embed([artifact.content])
            if embed_result.failure:
                return False

            embedding = embed_result.data[0]

            # Store with semantic infrastructure
            async with aiosqlite.connect(self.db_path) as db:
                result = await add_sqlite_vector(
                    db_connection=db,
                    user_id=artifact.user_id,
                    content=artifact.content,
                    metadata={
                        "topic": artifact.topic,
                        "confidence": artifact.confidence,
                        "context": artifact.context,
                        "created_at": artifact.created_at.isoformat(),
                        "updated_at": artifact.updated_at.isoformat(),
                        "source_conversations": artifact.source_conversations,
                        **artifact.metadata,
                    },
                    embedding=embedding,
                )

            return result.success

        except Exception:
            return False

    async def search_knowledge(
        self, query: str, user_id: str = "default", top_k: int = 5, threshold: float = 0.7
    ) -> list["KnowledgeArtifact"]:
        """Search knowledge artifacts using semantic similarity."""
        await self._ensure_schema()

        try:
            from datetime import datetime

            from cogency.knowledge import KnowledgeArtifact
            from cogency.providers import detect_embed
            from cogency.semantic import semantic_search

            embedder = detect_embed()

            async with aiosqlite.connect(self.db_path) as db:
                search_result = await semantic_search(
                    embedder=embedder,
                    query=query,
                    db_connection=db,
                    user_id=user_id,
                    top_k=top_k,
                    threshold=threshold,
                )

            if search_result.failure:
                return []

            # Convert search results to KnowledgeArtifact objects
            artifacts = []
            for result in search_result.data:
                metadata = result.get("metadata", {})

                # Reconstruct artifact from metadata
                artifact = KnowledgeArtifact(
                    topic=metadata.get("topic", "Unknown"),
                    content=result["content"],
                    confidence=metadata.get("confidence", 0.8),
                    context=metadata.get("context", ""),
                    user_id=user_id,
                    created_at=datetime.fromisoformat(
                        metadata.get("created_at", datetime.now().isoformat())
                    ),
                    updated_at=datetime.fromisoformat(
                        metadata.get("updated_at", datetime.now().isoformat())
                    ),
                    source_conversations=metadata.get("source_conversations", []),
                    metadata={
                        k: v
                        for k, v in metadata.items()
                        if k
                        not in [
                            "topic",
                            "confidence",
                            "context",
                            "created_at",
                            "updated_at",
                            "source_conversations",
                        ]
                    },
                )
                artifacts.append(artifact)

            return artifacts

        except Exception:
            return []

    async def load_knowledge(self, topic: str, user_id: str) -> "KnowledgeArtifact | None":
        """Load specific knowledge artifact by topic."""
        artifacts = await self.search_knowledge(f"topic:{topic}", user_id, top_k=1, threshold=0.9)
        return artifacts[0] if artifacts else None

    @state_event("knowledge_deleted", extract_delete_data)
    async def delete_knowledge(self, topic: str, user_id: str) -> bool:
        """Delete knowledge artifact by topic."""
        await self._ensure_schema()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    """DELETE FROM knowledge_vectors
                       WHERE user_id = ? AND json_extract(metadata, '$.topic') = ?""",
                    (user_id, topic),
                )
                await db.commit()
                return cursor.rowcount > 0

        except Exception:
            return False
