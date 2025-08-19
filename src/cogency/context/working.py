"""Working memory - tool history."""

import copy
from threading import Lock
from typing import Any


class WorkingMemory:
    """User-scoped working memory for tool execution history."""

    def __init__(self):
        self._storage: dict[str, list[dict[str, Any]]] = {}
        self._lock = Lock()

    def format(self, tool_results: list = None) -> str:
        """Format tool execution history for display."""
        if not tool_results:
            return ""

        recent = tool_results[-3:]
        lines = []
        for r in recent:
            name = r.get("tool", "unknown")
            if "result" in r:
                preview = str(r["result"])[:100]
                if len(str(r["result"])) > 100:
                    preview += "..."
                lines.append(f"✅ {name}: {preview}")
            else:
                error = r.get("error", "Unknown error")
                lines.append(f"❌ {name}: {error}")

        return "Working memory:\n" + "\n".join(lines)

    def get(self, user_id: str) -> list[dict[str, Any]]:
        """Get working memory for user."""
        if user_id is None:
            raise ValueError("user_id cannot be None")

        with self._lock:
            if user_id not in self._storage:
                self._storage[user_id] = []
            return copy.deepcopy(self._storage[user_id])

    def update(self, user_id: str, tool_results: list[dict[str, Any]]) -> None:
        """Update working memory for user."""
        if user_id is None:
            raise ValueError("user_id cannot be None")
        if tool_results is None:
            tool_results = []

        with self._lock:
            self._storage[user_id] = copy.deepcopy(tool_results)

    def clear(self, user_id: str) -> None:
        """Clear working memory after task completion."""
        if user_id is None:
            raise ValueError("user_id cannot be None")

        with self._lock:
            if user_id in self._storage:
                self._storage[user_id] = []

    def stats(self) -> dict[str, int]:
        """Get memory usage statistics for debugging."""
        with self._lock:
            return {
                "active_users": len(self._storage),
                "total_entries": sum(len(entries) for entries in self._storage.values()),
            }


# Singleton instance
working = WorkingMemory()
