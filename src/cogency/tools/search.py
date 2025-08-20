"""Search tool - DuckDuckGo web search."""

from ..core.protocols import Tool
from ..lib.result import Err, Ok, Result


class Search(Tool):
    """Search the web using DuckDuckGo."""

    def __init__(self, max_results: int = 5, performance_cap: int = 10):
        self.max_results = max_results
        self.performance_cap = performance_cap

    @property
    def name(self) -> str:
        return "search"

    @property
    def description(self) -> str:
        return f"Search the web. Args: query (str), limit (int, default {self.max_results})"

    async def execute(self, query: str, limit: int = None) -> Result[str, str]:
        """Execute web search."""
        try:
            from ddgs import DDGS
        except ImportError:
            return Err("DuckDuckGo search not available - install ddgs")

        if not query:
            return Err("Search query cannot be empty")

        # Use instance default or parameter override
        effective_limit = limit if limit is not None else self.max_results
        effective_limit = min(effective_limit, self.performance_cap)

        try:
            results = DDGS().text(query, max_results=effective_limit)

            if not results:
                return Ok("No search results found")

            # Format results for LLM consumption
            formatted = []
            for i, result in enumerate(results, 1):
                title = result.get("title", "No title")
                body = result.get("body", "No description")
                href = result.get("href", "No URL")

                formatted.append(f"{i}. {title}\n   {body}\n   URL: {href}")

            return Ok("\n\n".join(formatted))

        except Exception as e:
            return Err(f"Search failed: {str(e)}")
