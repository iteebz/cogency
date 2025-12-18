from dataclasses import dataclass
from typing import Annotated, Any

from cogency.core.protocols import ToolParam, ToolResult
from cogency.core.security import safe_execute
from cogency.core.tool import tool


@dataclass
class SearchParams:
    query: Annotated[
        str, ToolParam(description="Search query (keywords or phrase)", max_length=500)
    ]


@tool("Search the web. Returns up to 5 results with title, body, and URL.")
@safe_execute
async def Search(
    params: SearchParams,
    **kwargs: Any,
) -> ToolResult:
    if not params.query or not params.query.strip():
        return ToolResult(outcome="Search query cannot be empty", error=True)

    try:
        from ddgs import DDGS  # type: ignore[reportUnknownVariableType]
    except ImportError:
        return ToolResult(
            outcome="DDGS metasearch not available. Install with: pip install ddgs", error=True
        )

    effective_limit = 5

    results: list[dict[str, str]] = DDGS().text(params.query.strip(), max_results=effective_limit)

    if not results:
        return ToolResult(
            outcome=f"Found 0 results for '{params.query}'", content="No results found"
        )

    formatted: list[str] = []
    for result in results:
        title = result.get("title", "No title")
        body = result.get("body", "No description")
        href = result.get("href", "No URL")
        formatted.append(f"{title}\n{body}\n{href}")

    content = "\n\n".join(formatted)
    outcome = f"Found {len(results)} results for '{params.query}'"
    return ToolResult(outcome=outcome, content=content)
