"""Web search tool - DuckDuckGo integration with rate limiting and result formatting."""

import logging
from dataclasses import dataclass
from typing import Any, Dict

from ddgs import DDGS
from resilient_result import Result

from cogency.tools.base import Tool
from cogency.tools.registry import tool

logger = logging.getLogger(__name__)


@dataclass
class SearchArgs:
    query: str
    max_results: int = 5


@tool
class Search(Tool):
    def __init__(self):
        super().__init__(
            name="search",
            description="Search the web using DuckDuckGo for current information and answers to questions.",
            schema="search(query: str, max_results: int = 5)",
            emoji="🔍",
            args=SearchArgs,
            examples=[
                "search(query='latest AI developments 2024')",
                "search(query='Python async programming', max_results=3)",
                "search(query='weather London today')",
            ],
            rules=[
                "Use specific queries, avoid repetitive searches",
            ],
        )
        # Use base class formatting with templates
        self.arg_key = "query"
        self.human_template = "{message}:\n{results_summary}"
        self.agent_template = "{message}\n{results_summary}"

    async def run(self, query: str, max_results: int = 5, **kwargs) -> Dict[str, Any]:
        # Schema validation handles required args and basic types
        # Validate query is not empty or just whitespace
        if not query or not query.strip():
            return Result.fail("Search query cannot be empty")

        query = query.strip()  # Clean the query

        # Apply business logic constraints
        if max_results > 10:
            max_results = 10  # Cap at 10 results
        # Simple rate limiting - reduced for evals
        import asyncio

        await asyncio.sleep(0.5)  # 0.5 second delay
        # Perform search
        ddgs = DDGS()
        try:
            results = list(ddgs.text(query, max_results=max_results))
            if not results:
                logger.warning(f"DDGS returned no results for query: {query}")
        except Exception as e:
            logger.error(f"DDGS search failed for query '{query}': {e}")
            return Result.fail(f"DuckDuckGo search failed: {str(e)}")
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
            return Result.ok(
                {
                    "results": [],
                    "query": query,
                    "total_found": 0,
                    "message": "No results found for your query",
                    "results_summary": "No results available",
                }
            )
        # Create formatted summary for agent context
        results_summary = []
        for i, result in enumerate(formatted_results[:3], 1):  # Show top 3 results
            results_summary.append(f"{i}. {result['title']}: {result['snippet'][:100]}...")

        return Result.ok(
            {
                "results": formatted_results,
                "query": query,
                "total_found": len(formatted_results),
                "message": f"Found {len(formatted_results)} results for '{query}'",
                "results_summary": "\n".join(results_summary),
            }
        )
