"""Memory recall with SQLite fuzzy search instead of embeddings.

Architectural decision: SQLite LIKE patterns over vector embeddings.

Tradeoffs:
- 80% of semantic value for 20% of complexity
- No vector database infrastructure required
- Transparent search - users can understand and debug the queries
- No embedding model dependencies or API costs
"""

import time

from ...core.protocols import Tool, ToolResult
from ...lib.logger import logger
from ...lib.storage import MessageMatch, Storage
from ..security import safe_execute


class Recall(Tool):
    """Search memory."""

    name = "recall"
    description = "Search memory. Fuzzy search past user messages, 3 matches."
    schema = {
        "query": {
            "description": "Keywords to search for in past user messages",
            "required": True,
        }
    }

    def __init__(self, storage: Storage):
        self.storage = storage

    def describe(self, args: dict) -> str:
        return f'Recalling "{args.get("query", "query")}"'

    @safe_execute
    async def execute(
        self, query: str, conversation_id: str = None, user_id: str = None, **kwargs
    ) -> ToolResult:
        """Execute fuzzy search on past user messages."""
        if not query or not query.strip():
            return ToolResult(outcome="Search query cannot be empty", error=True)

        if not user_id:
            return ToolResult(outcome="User ID required for memory recall", error=True)

        query = query.strip()

        current_timestamps = await self._get_timestamps(conversation_id)

        matches = await self._search_messages(
            query=query,
            user_id=user_id,
            exclude_timestamps=current_timestamps,
            limit=3,
        )

        if not matches:
            outcome = f"Memory searched for '{query}' (0 matches)"
            content = "No past references found outside current conversation"
            return ToolResult(outcome=outcome, content=content)

        outcome = f"Memory searched for '{query}' ({len(matches)} matches)"
        content = self._format_matches(matches, query)
        return ToolResult(outcome=outcome, content=content)

    async def _get_timestamps(self, conversation_id: str) -> list[float]:
        """Get timestamps of current context window to exclude from search."""
        try:
            messages = await self.storage.load_messages_by_conversation_id(
                conversation_id=conversation_id, limit=20
            )
            return [msg["timestamp"] for msg in messages]
        except Exception as e:
            logger.warning(f"Recent messages lookup failed: {e}")
            return []

    async def _search_messages(
        self, query: str, user_id: str, exclude_timestamps: list[float], limit: int = 3
    ) -> list[MessageMatch]:
        """Fuzzy search user messages with SQLite pattern matching.\" """

        try:
            return await self.storage.search_messages(
                query=query,
                user_id=user_id,
                exclude_timestamps=exclude_timestamps,
                limit=limit,
            )
        except Exception as e:
            logger.warning(f"Message search failed: {e}")
            return []

    def _format_matches(self, matches: list[MessageMatch], query: str) -> str:
        """Format search results for ToolResult content."""
        results = []
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
