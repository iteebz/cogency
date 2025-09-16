"""Memory recall with SQLite fuzzy search instead of embeddings.

Architectural decision: SQLite LIKE patterns over vector embeddings.

Tradeoffs:
- 80% of semantic value for 20% of complexity
- No vector database infrastructure required
- Transparent search - users can understand and debug the queries
- No embedding model dependencies or API costs
"""

import sqlite3
import time
from typing import NamedTuple

from ...core.protocols import Tool, ToolResult
from ...lib.logger import logger
from ...lib.paths import Paths
from ..security import safe_execute


class MessageMatch(NamedTuple):
    """Past message match result."""

    content: str
    timestamp: float
    conversation_id: str


class MemoryRecall(Tool):
    """Recall past user messages outside current context window using fuzzy search."""

    name = "recall"
    description = "Search past user messages for context outside current conversation"
    schema = {
        "query": {
            "description": "Keywords to search for in past user messages",
            "required": True,
        }
    }

    def describe(self, args: dict) -> str:
        """Human-readable action description."""
        return f'Recalling "{args.get("query", "query")}"'

    @safe_execute
    async def execute(
        self, query: str, conversation_id: str = None, user_id: str = None, **kwargs
    ) -> ToolResult:
        """Execute fuzzy search on past user messages."""
        if not query or not query.strip():
            return ToolResult(outcome="Search query cannot be empty")

        if not user_id:
            return ToolResult(outcome="User ID required for memory recall")

        query = query.strip()

        # Get current context window to exclude
        current_timestamps = self._get_timestamps(conversation_id)

        # Simple SQL LIKE search of past user messages
        matches = self._search_messages(
            query=query,
            user_id=user_id,
            exclude_timestamps=current_timestamps,
            limit=3,
        )

        if not matches:
            outcome = f"Memory searched for '{query}'"
            content = "No past references found outside current conversation"
            return ToolResult(outcome=outcome, content=content)

        outcome = f"Memory searched for '{query}' ({len(matches)} matches)"
        content = self._format_matches(matches, query)
        return ToolResult(outcome=outcome, content=content)

    def _get_timestamps(self, conversation_id: str) -> list[float]:
        """Get timestamps of current context window to exclude from search."""
        if not conversation_id:
            return []

        db_path = Paths.db()

        try:
            with sqlite3.connect(db_path) as db:
                # Get last 20 user messages from current conversation
                rows = db.execute(
                    """
                    SELECT timestamp FROM conversations
                    WHERE conversation_id = ? AND type = 'user'
                    ORDER BY timestamp DESC
                    LIMIT 20
                """,
                    (conversation_id,),
                ).fetchall()

                return [row[0] for row in rows]
        except Exception as e:
            logger.warning(f"Recent messages lookup failed: {e}")
            return []

    def _search_messages(
        self, query: str, user_id: str, exclude_timestamps: list[float], limit: int = 3
    ) -> list[MessageMatch]:
        """Fuzzy search user messages with SQLite pattern matching."""
        db_path = Paths.db()

        # Build fuzzy search patterns
        keywords = query.lower().split()
        like_patterns = [f"%{keyword}%" for keyword in keywords]

        try:
            with sqlite3.connect(db_path) as db:
                # Build exclusion clause
                exclude_clause = ""
                params = []

                if exclude_timestamps:
                    placeholders = ",".join("?" for _ in exclude_timestamps)
                    exclude_clause = f"AND timestamp NOT IN ({placeholders})"
                    params.extend(exclude_timestamps)

                # Build LIKE clause for fuzzy matching
                like_clause = " OR ".join("LOWER(content) LIKE ?" for _ in like_patterns)
                params.extend(like_patterns)

                query_sql = f"""
                    SELECT content, timestamp, conversation_id,
                           (LENGTH(content) - LENGTH(REPLACE(LOWER(content), ?, ''))) as relevance_score
                    FROM conversations
                    WHERE type = 'user'
                    AND conversation_id LIKE ?
                    {exclude_clause}
                    AND ({like_clause})
                    ORDER BY relevance_score DESC, timestamp DESC
                    LIMIT ?
                """
                # Add relevance scoring query and user_id pattern as first parameters
                params.insert(0, query.lower())  # For relevance scoring
                params.insert(1, f"{user_id}%")  # For user scoping - includes exact match
                params.append(limit)

                rows = db.execute(query_sql, params).fetchall()

                return [
                    MessageMatch(
                        content=row[0],
                        timestamp=row[1],
                        conversation_id=row[2],
                        # Ignore row[3] which is relevance_score
                    )
                    for row in rows
                ]

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

            # Preview with highlighting (simple approach)
            content = match.content
            if len(content) > 100:
                content = content[:100] + "..."

            results.append(f"{time_ago}: {content}")

        return "\n".join(results)
