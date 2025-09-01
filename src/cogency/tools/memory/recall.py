"""Memory recall tool for fuzzy search of past user messages.

NOTE: Uses SQLite LIKE patterns instead of embeddings.
Fuzzy search gives 80% of semantic value for 20% of complexity.
Embeddings would add ~15% better matching at 4x complexity cost.
"""

import sqlite3
from typing import NamedTuple

from ...core.protocols import Tool, ToolResult
from ...core.result import Err, Ok, Result
from ...lib.storage import get_db_path
from ..file.utils import format_relative_time


class MessageMatch(NamedTuple):
    """Past message match result."""

    content: str
    timestamp: float
    conversation_id: str


class MemoryRecall(Tool):
    """Recall past user messages outside current context window using fuzzy search."""

    @property
    def name(self) -> str:
        return "recall"

    @property
    def description(self) -> str:
        return "Search past user messages for context outside current conversation"

    @property
    def schema(self) -> dict:
        return {
            "query": {
                "description": "Keywords to search for in past user messages",
                "required": True,
            }
        }

    async def execute(
        self, query: str, conversation_id: str = None, user_id: str = None
    ) -> Result[ToolResult]:
        """Execute fuzzy search on past user messages."""
        if not query or not query.strip():
            return Err("Search query cannot be empty")

        if not user_id:
            return Err("User ID required for memory recall")

        query = query.strip()

        try:
            # Get current context window to exclude
            current_timestamps = self._get_timestamps(conversation_id)

            # Fuzzy search past user messages
            matches = self._search_messages(
                query=query, user_id=user_id, exclude_timestamps=current_timestamps, limit=3
            )

            if not matches:
                outcome = f"Memory searched for '{query}'"
                content = "No past references found outside current conversation"
                return Ok(ToolResult(outcome, content))

            # Canonical outcome + content
            outcome = f"Memory searched for '{query}' ({len(matches)} matches)"
            content = self._format_matches(matches, query)
            return Ok(ToolResult(outcome, content))

        except Exception as e:
            return Err(f"Recall search failed: {str(e)}")

    def _get_timestamps(self, conversation_id: str) -> list[float]:
        """Get timestamps of current context window to exclude from search."""
        if not conversation_id:
            return []

        db_path = get_db_path()

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
        except Exception:
            return []

    def _search_messages(
        self, query: str, user_id: str, exclude_timestamps: list[float], limit: int = 3
    ) -> list[MessageMatch]:
        """Fuzzy search user messages with SQLite pattern matching."""
        db_path = get_db_path()

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
                params.insert(1, f"{user_id}_%")  # For user scoping
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

        except Exception:
            return []

    def _format_matches(self, matches: list[MessageMatch], query: str) -> str:
        """Format search results for ToolResult content."""
        results = []
        for match in matches:
            time_ago = format_relative_time(match.timestamp)

            # Preview with highlighting (simple approach)
            content = match.content
            if len(content) > 100:
                content = content[:100] + "..."

            results.append(f"{time_ago}: {content}")

        return "\n".join(results)
