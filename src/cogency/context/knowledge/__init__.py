"""Knowledge subdomain - extraction, synthesis and retrieval systems."""

from typing import Optional

from .extract import extract
from .retrieve import Retrieve
from .types import KnowledgeArtifact


async def build_knowledge_context(query: str, user_id: str) -> Optional[str]:
    """Build knowledge context with automatic retrieval.

    Args:
        query: User query for knowledge retrieval
        user_id: User identifier for scoped knowledge

    Returns:
        Knowledge context string or None
    """
    from cogency.events import emit

    try:
        import aiosqlite

        from cogency.config import PathsConfig
        from cogency.providers import detect_embed
        from cogency.semantic import semantic_search

        embedder = detect_embed()
        # Functional operations handle schema automatically

        paths = PathsConfig()
        db_path = paths.get_data_path() / "knowledge.db"

        async with aiosqlite.connect(db_path) as db:
            search_result = await semantic_search(
                embedder=embedder,
                query=query,
                db_connection=db,
                user_id=user_id,
                top_k=3,
                threshold=0.75,
            )

        if search_result.failure or not search_result.unwrap():
            return None

        knowledge_items = []
        for result in search_result.unwrap()[:2]:
            topic = result["metadata"].get("topic", "Knowledge")
            content = result["content"][:200]
            knowledge_items.append(f"- {topic}: {content}...")

        emit("knowledge", operation="auto_retrieval", results=len(knowledge_items), query=query)
        return "RELEVANT KNOWLEDGE:\n" + "\n".join(knowledge_items)

    except Exception as e:
        emit("knowledge", operation="auto_retrieval", status="error", error=str(e))
        return None


__all__ = ["build_knowledge_context", "extract", "Retrieve", "KnowledgeArtifact"]
