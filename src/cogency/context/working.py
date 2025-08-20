"""Working memory - tool history."""

import copy
from threading import Lock
from typing import Any


class WorkingMemory:
    """Task-scoped working memory for tool execution history."""

    def __init__(self):
        self._storage: dict[str, list[dict[str, Any]]] = {}
        self._lock = Lock()

    def format(self, task_id: str, limit: int = 3) -> str:
        """Inject working memory context for LLM reasoning."""
        actions = self.get(task_id)
        if not actions:
            return ""

        # Show recent tool results for LLM context
        recent = actions[-limit:] if len(actions) > limit else actions
        context_lines = []
        for action in recent:
            tool = action.get("tool", "unknown")
            args = action.get("args", {})
            if "result" in action:
                result = action["result"]
                context_lines.append(f"✓ {tool}({args}) → {result}")
            elif "error" in action:
                error = action["error"]
                context_lines.append(f"✗ {tool}({args}) → Error: {error}")

        return "Recent actions:\n" + "\n".join(context_lines)

    def get(self, task_id: str) -> list[dict[str, Any]]:
        """Get working memory for task."""
        if task_id is None:
            raise ValueError("task_id cannot be None")

        with self._lock:
            if task_id not in self._storage:
                self._storage[task_id] = []
            return copy.deepcopy(self._storage[task_id])

    def update(self, task_id: str, tool_results: list[dict[str, Any]]) -> None:
        """Update working memory for task."""
        if task_id is None:
            return
        if tool_results is None:
            tool_results = []

        with self._lock:
            self._storage[task_id] = copy.deepcopy(tool_results)

    def clear(self, task_id: str) -> None:
        """Clear working memory after task completion."""
        if task_id is None:
            return

        with self._lock:
            if task_id in self._storage:
                del self._storage[task_id]

    def actions(self, task_id: str, action_result: dict) -> None:
        """Record action taken in working memory."""
        if task_id is None:
            return

        with self._lock:
            if task_id not in self._storage:
                self._storage[task_id] = []
            self._storage[task_id].append(copy.deepcopy(action_result))


# Singleton instance
working = WorkingMemory()
