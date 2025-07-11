import time
from typing import Any, Dict, List

from ddgs import DDGS

from cogency.tools.base import BaseTool


class WebSearchTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="web_search",
            description="Search the web using DuckDuckGo for current information and answers to questions.",
        )
        self._last_search_time = 0
        self._min_delay = 1.0  # Minimum delay between searches in seconds

    def run(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        # Input validation
        if not query or not query.strip():
            return {"error": "Query cannot be empty"}

        if not isinstance(max_results, int) or max_results <= 0:
            return {"error": "max_results must be a positive integer"}

        if max_results > 10:
            max_results = 10  # Cap at 10 results

        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self._last_search_time
        if time_since_last < self._min_delay:
            time.sleep(self._min_delay - time_since_last)

        try:
            # Perform search
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))

            self._last_search_time = time.time()

            if not results:
                return {
                    "results": [],
                    "query": query,
                    "total_found": 0,
                    "message": "No results found for your query",
                }

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

            return {
                "results": formatted_results,
                "query": query,
                "total_found": len(formatted_results),
            }

        except Exception as e:
            return {
                "error": f"Search failed: {str(e)}",
                "query": query,
                "total_found": 0,
            }

    def get_schema(self) -> str:
        return "web_search(query='search terms', max_results=5)"

    def get_usage_examples(self) -> List[str]:
        return [
            "web_search(query='Python programming tutorials', max_results=3)",
            "web_search(query='latest AI developments 2024')",
            "web_search(query='how to install Docker', max_results=5)",
        ]
