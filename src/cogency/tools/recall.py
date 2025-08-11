"""CANONICAL Recall tool - semantic search over dynamic agent memory."""

from dataclasses import dataclass

from resilient_result import Result

from cogency.semantic import semantic_search
from cogency.storage.state import SQLite
from cogency.tools.base import Tool
from cogency.tools.registry import tool


@dataclass
class RecallArgs:
    query: str
    top_k: int = 5
    threshold: float = 0.7


@tool
class Recall(Tool):
    """Semantic search over accumulated conversation knowledge.
    
    Searches agent's memory using SQLite vector storage.
    Knowledge is automatically extracted and stored from conversations.
    """

    def __init__(self, top_k: int = 3, min_similarity: float = 0.7, embedder=None):
        super().__init__(
            name="recall",
            description="Search accumulated knowledge from previous conversations",
            schema="recall(query: str, top_k: int = 5, threshold: float = 0.7)",
            emoji="🧠",
            args=RecallArgs,
            examples=[
                "recall(query='python performance tips')",
                "recall(query='database optimization techniques', top_k=5)",
                "recall(query='react best practices', threshold=0.8)",
            ],
            rules=[
                "Use specific, descriptive queries for better results",
                "Lower threshold (0.6) for broader results",
                "Higher threshold (0.8) for more precise results",
                "Searches only user's own conversation history",
            ],
        )
        
        self.default_top_k = top_k
        self.min_similarity = min_similarity
        
        # CANONICAL: Injected embedder from agent
        self._embedder = embedder

    async def run(
        self,
        query: str,
        user_id: str = "default",
        top_k: int = None,
        threshold: float = None,
        **kwargs,
    ) -> Result:
        """Search agent's memory for relevant knowledge."""
        if not query or not query.strip():
            return Result.fail("Search query cannot be empty")

        if not self._embedder:
            return Result.fail("No embedder configured - must be injected from agent")

        # Use defaults if not specified
        top_k = top_k or self.default_top_k
        threshold = threshold if threshold is not None else self.min_similarity

        # Get SQLite connection
        store = SQLite()
        await store._ensure_schema()

        # CANONICAL semantic search using SQLite
        import aiosqlite
        async with aiosqlite.connect(store.db_path) as db:
            search_result = await semantic_search(
                embedder=self._embedder,
                query=query.strip(),
                db_connection=db,
                user_id=user_id,
                top_k=top_k,
                threshold=threshold,
            )

        if search_result.failure:
            return Result.fail(f"Memory search failed: {search_result.error}")

        results = search_result.data

        if not results:
            return Result.ok({
                "response": self._format_no_results(query),
                "count": 0,
                "results": [],
            })

        # Format for agent consumption
        formatted_response = self._format_results(results, query)

        return Result.ok({
            "response": formatted_response,
            "count": len(results),
            "results": results,
            "topics": [r["metadata"].get("topic", "Unknown") for r in results],
            "similarities": [r["similarity"] for r in results],
        })

    def _format_results(self, results: list[dict], query: str) -> str:
        """Format search results for agent consumption."""
        response_parts = [
            f"## 🧠 Memory Recall: '{query}'\n",
            f"Found {len(results)} relevant knowledge items:\n",
        ]

        for i, result in enumerate(results, 1):
            content = result["content"]
            similarity = result["similarity"]
            topic = result["metadata"].get("topic", "Unknown Topic")
            
            # Extract preview from content
            preview = self._extract_preview(content)
            
            response_parts.append(
                f"### {i}. {topic} (similarity: {similarity:.2f})\n"
                f"{preview}\n"
            )

        return "\n".join(response_parts)

    def _format_no_results(self, query: str) -> str:
        """Format response when no results found."""
        return (
            f"## 🧠 Memory Recall: '{query}'\n\n"
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
        if last_sentence > max_length * 0.7:
            return preview[:last_sentence + 1]

        # Otherwise break at word boundary
        last_space = preview.rfind(" ")
        if last_space > 0:
            return preview[:last_space] + "..."

        return preview + "..."

    # Tool display formatting
    human_template = "🧠 Searching memory: '{query}'"
    agent_template = "Found {count} relevant memories"
    arg_key = "query"