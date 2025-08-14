"""SQLite knowledge operations - semantic memory persistence."""

from pathlib import Path
from typing import TYPE_CHECKING

import aiosqlite

if TYPE_CHECKING:
    from cogency.context.knowledge import KnowledgeArtifact

from ...events.orchestration import domain_event, extract_delete_data, extract_knowledge_data


async def _ensure_schema(db_path: str):
    """Ensure knowledge schema exists."""
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_vectors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                embedding TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_knowledge_user ON knowledge_vectors(user_id)"
        )
        await db.commit()


def _get_db_path(db_path: str = None) -> str:
    """Get database path with defaults."""
    if db_path is None:
        from cogency.config.paths import paths

        base_path = Path(paths.base_dir)
        base_path.mkdir(exist_ok=True)
        db_path = base_path / "store.db"

    if db_path == ":memory:" or str(db_path).startswith(":memory:"):
        return str(db_path)
    return str(Path(db_path).expanduser().resolve())


@domain_event("knowledge_saved", extract_knowledge_data)
async def save_knowledge_vector(artifact: "KnowledgeArtifact", db_path: str = None) -> bool:
    """Save knowledge artifact with semantic embedding storage."""
    db_path = _get_db_path(db_path)
    await _ensure_schema(db_path)

    try:
        from cogency.providers import detect_embed
        from cogency.semantic import add_sqlite_vector

        # Generate embedding for semantic search
        embedder = detect_embed()
        embed_result = await embedder.embed([artifact.content])
        if embed_result.failure:
            return False

        embedding = embed_result.unwrap()[0]

        # Store with semantic infrastructure
        async with aiosqlite.connect(db_path) as db:
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


async def search_knowledge_vectors(
    query: str,
    user_id: str = "default",
    top_k: int = 5,
    threshold: float = 0.7,
    db_path: str = None,
) -> list["KnowledgeArtifact"]:
    """Search knowledge artifacts using semantic similarity."""
    db_path = _get_db_path(db_path)
    await _ensure_schema(db_path)

    try:
        from datetime import datetime

        from cogency.context.knowledge import KnowledgeArtifact
        from cogency.providers import detect_embed
        from cogency.semantic import semantic_search

        embedder = detect_embed()

        async with aiosqlite.connect(db_path) as db:
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
        for result in search_result.unwrap():
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


@domain_event("knowledge_deleted", extract_delete_data)
async def delete_knowledge_vector(topic: str, user_id: str, db_path: str = None) -> bool:
    """Delete knowledge artifact by topic."""
    db_path = _get_db_path(db_path)
    await _ensure_schema(db_path)

    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute(
                """DELETE FROM knowledge_vectors
                   WHERE user_id = ? AND json_extract(metadata, '$.topic') = ?""",
                (user_id, topic),
            )
            await db.commit()
            return cursor.rowcount > 0

    except Exception:
        return False
