"""Web search using DDGS metasearch with clean result formatting."""

from ...core.protocols import Tool, ToolResult
from ..security import safe_execute


class WebSearch(Tool):
    """DDGS metasearch (multiple backends) with structured result formatting."""

    name = "web_search"
    description = "Search the web for information"
    schema = {"query": {}}

    def describe(self, args: dict) -> str:
        """Human-readable action description."""
        return f'Web searching "{args.get("query", "query")}"'

    @safe_execute
    async def execute(self, query: str, **kwargs) -> ToolResult:
        """Execute clean web search."""
        if not query or not query.strip():
            return ToolResult(outcome="Search query cannot be empty")

        try:
            from ddgs import DDGS
        except ImportError:
            return ToolResult(
                outcome="DDGS metasearch not available. Install with: pip install ddgs"
            )

        effective_limit = 5  # Default search results

        results = DDGS().text(query.strip(), max_results=effective_limit)

        if not results:
            return ToolResult(outcome=f"No results for '{query}'", content=None)

        formatted = []
        for result in results:
            title = result.get("title", "No title")
            body = result.get("body", "No description")
            href = result.get("href", "No URL")
            formatted.append(f"{title}\n{body}\n{href}")

        content = "\n\n".join(formatted)
        outcome = f"Found {len(results)} results for '{query}'"
        return ToolResult(outcome=outcome, content=content)
