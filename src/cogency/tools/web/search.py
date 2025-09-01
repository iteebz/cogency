"""Web search tool."""

from ...core.protocols import Tool, ToolResult
from ...core.result import Err, Ok, Result


class WebSearch(Tool):
    """Clean web search with intelligent output formatting."""

    def __init__(self):
        pass

    @property
    def name(self) -> str:
        return "search"

    @property
    def description(self) -> str:
        return "Search the web for information"

    @property
    def schema(self) -> dict:
        return {"query": {}}

    async def execute(self, query: str, **kwargs) -> Result[ToolResult]:
        """Execute clean web search."""
        if not query or not query.strip():
            return Err("Search query cannot be empty")

        # Check dependencies
        try:
            from ddgs import DDGS
        except ImportError:
            return Err("DuckDuckGo search not available. Install with: pip install ddgs")

        # Use default limit
        from ..constants import SEARCH_DEFAULT_RESULTS

        effective_limit = SEARCH_DEFAULT_RESULTS

        try:
            results = DDGS().text(query.strip(), max_results=effective_limit)

            if not results:
                outcome = f"Search completed for '{query}'"
                content = "No results found"
                return Ok(ToolResult(outcome, content))

            # Canonical result formatting
            formatted = []
            for result in results:
                title = result.get("title", "No title")
                body = result.get("body", "No description")
                href = result.get("href", "No URL")

                formatted.append(f"{title}\n{body}\n{href}")

            # Canonical outcome + content
            outcome = f"Search completed for '{query}' ({len(results)} results)"
            content = "\n\n".join(formatted)
            return Ok(ToolResult(outcome, content))

        except Exception as e:
            return Err(f"Search failed: {str(e)}")
