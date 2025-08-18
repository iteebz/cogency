"""Retrieve: Search knowledge base for relevant documents."""

from ..lib.storage import search_documents
from .base import Tool


class Retrieve(Tool):
    """Search knowledge base for relevant documents."""

    @property
    def name(self) -> str:
        return "retrieve"

    @property
    def description(self) -> str:
        return (
            "Search knowledge base for documents. Args: query (str), limit (int, optional, max 5)"
        )

    async def execute(self, query: str, limit: int = 3) -> str:
        try:
            # Limit to max 5 results
            limit = min(limit, 5)
            results = search_documents(query, limit)

            if not results:
                return f"📭 No documents found for: {query}"

            # Format results
            formatted = []
            for i, result in enumerate(results, 1):
                doc_id = result["doc_id"]
                content = result["content"][:200]
                if len(result["content"]) > 200:
                    content += "..."

                relevance = result["relevance"]
                formatted.append(f"{i}. {doc_id} (relevance: {relevance})\n   {content}")

            return f"🔍 Found {len(results)} documents:\n\n" + "\n\n".join(formatted)

        except Exception as e:
            return f"❌ Retrieve error: {str(e)}"
