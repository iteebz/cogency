"""Knowledge search."""

from ..storage import search_documents


def knowledge(query: str, user_id: str) -> str:
    """Semantic search results."""
    try:
        results = search_documents(query, limit=3)
        if not results:
            return ""

        lines = []
        for r in results:
            content = r["content"][:150]
            if len(r["content"]) > 150:
                content += "..."
            lines.append(f"📄 {r['doc_id']}: {content}")

        return "Relevant knowledge:\n" + "\n\n".join(lines)
    except Exception:
        return ""
