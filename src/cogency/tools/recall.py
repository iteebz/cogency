"""Recall tool for semantic memory retrieval."""

from dataclasses import dataclass
from typing import Any, Dict, List

from resilient_result import Result

from cogency.tools.base import Tool
from cogency.tools.registry import tool


@dataclass
class RecallArgs:
    """Arguments for Recall tool."""

    query: str
    layer: str = "topics"  # Currently only "topics" for Phase 1
    limit: int = 3
    min_similarity: float = 0.7


@tool
class Recall(Tool):
    """Tool for retrieving knowledge from archival memory.

    Searches accumulated topic artifacts using semantic similarity.
    Provides agents with access to cross-conversation learning.
    """

    def __init__(self, archival_memory=None):
        super().__init__(
            name="recall",
            description="Search accumulated knowledge from previous conversations",
            schema="recall(query='python optimization', layer='topics', limit=3)",
            emoji="🧠",
            args=RecallArgs,
            examples=[
                "recall(query='python performance tips')",
                "recall(query='database optimization techniques', limit=5)",
                "recall(query='react best practices', min_similarity=0.6)",
            ],
            rules=[
                "Use specific, descriptive queries for better results",
                "Lower min_similarity (0.6) for broader results",
                "Higher min_similarity (0.8) for more precise results",
                "Layer 'topics' is the only available option in Phase 1",
            ],
        )
        self.archival = archival_memory
        self.user_id = "default"  # Will be set by agent context

    def set_context(self, user_id: str, archival_memory) -> None:
        """Set user context and archival memory reference."""
        self.user_id = user_id
        self.archival = archival_memory

    async def run(
        self,
        query: str,
        layer: str = "topics",
        limit: int = 3,
        min_similarity: float = 0.7,
        **kwargs,
    ) -> Result:
        """Search archival memory for relevant knowledge.

        Args:
            query: Search query describing what to recall
            layer: Memory layer to search ("topics" only in Phase 1)
            limit: Maximum number of results to return
            min_similarity: Minimum similarity threshold (0.0-1.0)

        Returns:
            Result containing formatted search results
        """
        from resilient_result import Err, Ok

        from cogency.events import emit

        if not self.archival:
            return Err("Archival memory not initialized")

        if layer != "topics":
            return Err(f"Layer '{layer}' not supported in Phase 1. Use 'topics'.")

        try:
            emit("tool", operation="recall", query=query, layer=layer, status="start")

            # Search archival memory
            results = await self.archival.search_topics(
                user_id=self.user_id, query=query, limit=limit, min_similarity=min_similarity
            )

            if not results:
                formatted_response = self._format_no_results(query)
                emit("tool", operation="recall", query=query, status="no_results")
                return Ok({"response": formatted_response, "count": 0})

            # Format results for agent consumption
            formatted_response = self._format_results(results, query)

            emit(
                "tool",
                operation="recall",
                query=query,
                status="complete",
                results_found=len(results),
            )

            return Ok(
                {
                    "response": formatted_response,
                    "count": len(results),
                    "topics": [r["topic"] for r in results],
                    "similarities": [r["similarity"] for r in results],
                }
            )

        except Exception as e:
            emit("tool", operation="recall", query=query, status="error", error=str(e))
            return Err(f"Memory recall failed: {str(e)}")

    def _format_results(self, results: List[Dict[str, Any]], query: str) -> str:
        """Format search results for agent consumption."""
        if not results:
            return self._format_no_results(query)

        response_parts = [
            f"## 🧠 Knowledge Recall: '{query}'\n",
            f"Found {len(results)} relevant knowledge items:\n",
        ]

        for i, result in enumerate(results, 1):
            topic = result.get("topic", "Unknown Topic")
            content = result.get("content", "")
            similarity = result.get("similarity", 0)
            updated = result.get("updated", "")

            # Extract preview from content
            content_preview = self._extract_preview(content)

            response_parts.append(
                f"### {i}. {topic} (similarity: {similarity:.2f})\n" f"{content_preview}\n"
            )

            if updated:
                response_parts.append(f"*Last updated: {updated[:10]}*\n")

        return "\n".join(response_parts)

    def _format_no_results(self, query: str) -> str:
        """Format response when no results found."""
        return (
            f"## 🧠 Knowledge Recall: '{query}'\n\n"
            "No relevant knowledge found in memory. This might be a new topic "
            "or the query might need to be more specific.\n\n"
            "Try:\n"
            "- Using more specific technical terms\n"
            "- Lowering the similarity threshold\n"
            "- Checking for alternative phrasing"
        )

    def _extract_preview(self, content: str, max_length: int = 300) -> str:
        """Extract a meaningful preview from content."""
        if not content:
            return "No content available."

        # Clean up content - remove excessive whitespace
        content = " ".join(content.split())

        if len(content) <= max_length:
            return content

        # Try to break at sentence boundary
        preview = content[:max_length]
        last_sentence = preview.rfind(".")
        if last_sentence > max_length * 0.7:  # If we can break at a reasonable sentence
            return preview[: last_sentence + 1]

        # Otherwise break at word boundary
        last_space = preview.rfind(" ")
        if last_space > 0:
            return preview[:last_space] + "..."

        return preview + "..."

    # Override formatting for cleaner tool display
    human_template = "🧠 Searching: '{query}'"
    agent_template = "Found {count} relevant knowledge items"
    arg_key = "query"


# Export for tool registration
__all__ = ["Recall"]
