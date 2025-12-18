"""Memory recall with SQLite fuzzy search instead of embeddings.

Architectural decision: SQLite LIKE patterns over vector embeddings.

Tradeoffs:
- 80% of semantic value for 20% of complexity
- No vector database infrastructure required
- Transparent search - users can understand and debug the queries
- No embedding model dependencies or API costs
"""

import logging
import time
from dataclasses import dataclass
from typing import Annotated, Any

from cogency.core.protocols import MessageMatch, Storage, ToolParam, ToolResult
from cogency.core.security import safe_execute
from cogency.core.tool import tool

logger = logging.getLogger(__name__)


@dataclass
class RecallParams:
    query: Annotated[
        str,
        ToolParam(
            description="Keywords or phrase to search for in past messages",
            max_length=200,
        ),
    ]


@tool("Search past conversations (excludes current). Use when user references prior context.")
@safe_execute
async def Recall(
    params: RecallParams,
    storage: Storage,
    conversation_id: str | None = None,
    user_id: str | None = None,
    **kwargs: Any,
) -> ToolResult:
    if not params.query or not params.query.strip():
        return ToolResult(outcome="Search query cannot be empty", error=True)

    if not user_id:
        return ToolResult(outcome="User ID required for memory recall", error=True)

    query = params.query.strip()
    matches = await storage.search_messages(
        query=query,
        user_id=user_id,
        exclude_conversation_id=conversation_id,
        limit=3,
    )

    if not matches:
        outcome = f"Memory searched for '{query}' (0 matches)"
        content = "No past references found outside current conversation"
        return ToolResult(outcome=outcome, content=content)

    outcome = f"Memory searched for '{query}' ({len(matches)} matches)"
    content = _format_matches(matches)
    return ToolResult(outcome=outcome, content=content)


def _format_matches(matches: list[MessageMatch]) -> str:
    results: list[str] = []
    for match in matches:
        time_diff = time.time() - match.timestamp
        if time_diff < 60:
            time_ago = "<1min ago"
        elif time_diff < 3600:
            time_ago = f"{int(time_diff / 60)}min ago"
        elif time_diff < 86400:
            time_ago = f"{int(time_diff / 3600)}h ago"
        else:
            time_ago = f"{int(time_diff / 86400)}d ago"

        content = match.content
        if len(content) > 100:
            content = content[:100] + "..."

        results.append(f"{time_ago}: {content}")

    return "\n".join(results)
