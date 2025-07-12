import time
from typing import Any, Dict, List

from ddgs import DDGS

from cogency.config import get_config
from cogency.tools.base import BaseTool
from cogency.utils.interrupt import interruptable
from cogency.utils.errors import (
    ToolError,
    ValidationError,
    create_success_response,
    handle_tool_exception,
    validate_required_params,
)


class WebSearchTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="web_search",
            description=(
                "Search the web using DuckDuckGo for current information and answers to questions."
            ),
        )
        self._last_search_time = 0
        # Get rate limit from config
        try:
            config = get_config()
            self._min_delay = config.web_rate_limit
        except Exception:
            # Fallback if config not available, log error in a real system
            self._min_delay = 1.0

    @handle_tool_exception
    @interruptable
    async def run(self, query: str, max_results: int = None) -> Dict[str, Any]:
        # Get default max_results from config if not provided
        if max_results is None:
            try:
                config = get_config()
                max_results = config.web_max_results
            except Exception:
                max_results = 5  # Fallback
        # Input validation
        validate_required_params({"query": query}, ["query"], self.name)

        if not isinstance(max_results, int) or max_results <= 0:
            raise ValidationError(
                "max_results must be a positive integer",
                error_code="INVALID_MAX_RESULTS",
                details={"max_results": max_results, "type": type(max_results).__name__},
            )

        if max_results > 10:
            max_results = 10  # Cap at 10 results

        # Rate limiting
        import asyncio

        current_time = time.time()
        time_since_last = current_time - self._last_search_time
        if time_since_last < self._min_delay:
            await asyncio.sleep(self._min_delay - time_since_last)

        # Perform search
        ddgs = DDGS()
        try:
            results = list(ddgs.text(query, max_results=max_results))
        except Exception as e:
            raise ToolError(
                f"DuckDuckGo search failed: {str(e)}",
                error_code="SEARCH_FAILED",
                details={"query": query, "max_results": max_results},
            )

        self._last_search_time = time.time()

        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append(
                {
                    "title": result.get("title", "No title"),
                    "snippet": result.get("body", "No snippet available"),
                    "url": result.get("href", "No URL"),
                }
            )

        if not formatted_results:
            return create_success_response(
                {
                    "results": [],
                    "query": query,
                    "total_found": 0,
                },
                "No results found for your query",
            )

        return create_success_response(
            {
                "results": formatted_results,
                "query": query,
                "total_found": len(formatted_results),
            },
            f"Found {len(formatted_results)} results for '{query}'",
        )

    def get_schema(self) -> str:
        return "web_search(query='search terms', max_results=5)"

    def get_usage_examples(self) -> List[str]:
        return [
            "web_search(query='Python programming tutorials', max_results=3)",
            "web_search(query='latest AI developments 2024')",
            "web_search(query='how to install Docker', max_results=5)",
        ]
