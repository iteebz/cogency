"""Search: Clean web search with intelligent output formatting."""

from ..core.protocols import Tool
from ..lib.result import Err, Ok, Result


class Search(Tool):
    """Clean web search with intelligent output formatting."""

    def __init__(self, max_results: int = 5, performance_cap: int = 10):
        self.max_results = max_results
        self.performance_cap = performance_cap

    @property
    def name(self) -> str:
        return "search"

    @property
    def description(self) -> str:
        return "Search the web. Args: query (str), limit (int, default 5)"

    @property
    def schema(self) -> dict:
        return {
            "query": {"type": "str", "required": True, "description": "Search query string"},
            "limit": {
                "type": "int",
                "required": False,
                "default": 5,
                "description": "Maximum number of results (max 10)",
            },
        }

    @property
    def examples(self) -> list[dict]:
        return [
            {
                "task": "Search programming topic",
                "call": {"query": "Python async programming best practices"},
            },
            {"task": "Find documentation", "call": {"query": "React hooks tutorial", "limit": 3}},
            {"task": "Research technology", "call": {"query": "machine learning frameworks 2024"}},
            {
                "task": "Get more results",
                "call": {"query": "JavaScript performance optimization", "limit": 8},
            },
        ]

    async def execute(self, query: str, limit: int = None) -> Result[str, str]:
        """Execute clean web search."""
        if not query or not query.strip():
            return Err("Search query cannot be empty")

        # Check dependencies
        try:
            from ddgs import DDGS
        except ImportError:
            return Err("DuckDuckGo search not available. Install with: pip install ddgs")

        # Determine result limit
        effective_limit = limit if limit is not None else self.max_results
        effective_limit = min(effective_limit, self.performance_cap)

        try:
            results = DDGS().text(query.strip(), max_results=effective_limit)

            if not results:
                return Ok(f"No search results found for '{query}'")

            # Clean result formatting
            formatted = []
            for i, result in enumerate(results, 1):
                title = result.get("title", "No title")
                body = result.get("body", "No description")
                href = result.get("href", "No URL")

                formatted.append(f"{i}. {title}\n   {body}\n   🔗 {href}")

            header = f"🔍 Search results for '{query}' ({len(results)} results)\n"
            return Ok(header + "\n".join(formatted))

        except Exception as e:
            return Err(f"Search failed: {str(e)}")
