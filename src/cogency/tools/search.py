from ..core.protocols import Tool, ToolResult
from ..core.security import safe_execute


class Search(Tool):
    """Search the web for high-signal summaries."""

    name = "search"
    description = "Search web. Returns up to 5 results with title/body/url."
    schema = {"query": {}}

    def describe(self, args: dict) -> str:
        return f'Web searching "{args.get("query", "query")}"'

    @safe_execute
    async def execute(self, query: str, **kwargs) -> ToolResult:
        if not query or not query.strip():
            return ToolResult(outcome="Search query cannot be empty", error=True)

        try:
            from ddgs import DDGS
        except ImportError:
            return ToolResult(
                outcome="DDGS metasearch not available. Install with: pip install ddgs", error=True
            )

        effective_limit = 5  # Default search results

        results = DDGS().text(query.strip(), max_results=effective_limit)

        if not results:
            return ToolResult(outcome=f"Found 0 results for '{query}'", content="No results found")

        formatted = []
        for result in results:
            title = result.get("title", "No title")
            body = result.get("body", "No description")
            href = result.get("href", "No URL")
            formatted.append(f"{title}\n{body}\n{href}")

        content = "\n\n".join(formatted)
        outcome = f"Found {len(results)} results for '{query}'"
        return ToolResult(outcome=outcome, content=content)
