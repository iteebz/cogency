"""Knowledge: Semantic search results for queries."""

from ..storage import search_documents


def knowledge(query: str, user_id: str) -> str:
    """Semantic search results for query."""
    try:
        results = search_documents(query, limit=3)
        if not results:
            return ""

        # Format search results
        formatted = []
        for result in results:
            content = result["content"][:150]  # Truncate
            if len(result["content"]) > 150:
                content += "..."
            formatted.append(f"📄 {result['doc_id']}: {content}")

        return "Relevant knowledge:\n" + "\n\n".join(formatted)
    except Exception:
        return ""  # Graceful degradation
