"""Recall tool for Cogency agents using BaseMemory."""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from resilient_result import Result

from cogency.memory import Store
from cogency.tools.base import Tool
from cogency.tools.registry import tool

logger = logging.getLogger(__name__)


@dataclass
class RecallArgs:
    query: str
    limit: Optional[int] = 5
    tags: Optional[List[str]] = None


@tool
class Recall(Tool):
    """Tool for retrieving content from agent memory."""

    def __init__(self, memory: Store):
        super().__init__(
            name="recall",
            description="Search memory for relevant information when user asks about themselves, their preferences, past interactions, or references things they've mentioned before. Use when current conversation lacks context the user expects you to know.",
            schema="recall(query: str, limit: int = 5, tags: list = None)",
            emoji="🧠",
            params=RecallArgs,
            examples=[
                "recall(query='user favorite color')",
                "recall(query='previous project discussion', limit=5)",
                "recall(query='technical preferences', tags=['coding'])",
            ],
            rules=[
                "Use this tool when the user asks about themselves, their preferences, past interactions, or references things they've mentioned before.",
                "Always provide a 'query' to search memory.",
                "Optionally use 'limit' to control the number of results (default is all relevant).",
                "Optionally use 'tags' (list of strings) to filter memory entries.",
            ],
        )
        self.memory = memory
        if memory is None:
            raise ValueError("Recall tool requires a memory backend, but None was provided")

    async def run(
        self, query: str, limit: Optional[int] = None, tags: Optional[list] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        """Retrieve content from memory."""
        tags = tags or []
        # Extract user_id from context if available
        context = kwargs.get("_context")
        user_id = getattr(context, "user_id", "default") if context else "default"
        try:
            artifacts = await self.memory.read(
                query=query, limit=limit, tags=tags if tags else None, user_id=user_id
            )
            results = []
            for artifact in artifacts:
                results.append(
                    {
                        "id": str(artifact.id),
                        "content": artifact.content,
                        "tags": artifact.tags,
                        "created_at": artifact.created_at.isoformat(),
                        "metadata": artifact.metadata,
                    }
                )
            return Result.ok(
                {
                    "query": query,
                    "results_count": len(results),
                    "results": results,
                }
            )
        except Exception as e:
            logger.error(f"Failed to recall content for query '{query}': {e}")
            return Result.fail(f"Failed to recall content: {str(e)}")

    def format_human(
        self, params: Dict[str, Any], results: Optional[Result] = None
    ) -> tuple[str, str]:
        """Format recall execution for display."""
        from cogency.utils import truncate

        query = params.get("query", "")
        param_str = f"({truncate(query, 30)})" if query else ""
        if results is None:
            return param_str, ""
        # Format results
        if results.failure:
            result_str = f"Error: {results.error}"
        else:
            data = results.data
            count = data.get("results_count", 0)
            result_str = f"Found {count} memories" if count > 0 else "No memories found"
        return param_str, result_str

    def format_agent(self, result_data: Dict[str, Any]) -> str:
        """Format recall results for agent action history."""
        if not result_data:
            return "No result"

        query = result_data.get("query", "")
        count = result_data.get("results_count", 0)
        results = result_data.get("results", [])

        if count > 0:
            first_content = results[0].get("content", "")
            return f"Found {count} memories for query '{query}'. First: {first_content[:70]}..."
        else:
            return f"No memories found for query '{query}"
