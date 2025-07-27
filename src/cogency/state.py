"""Cogency State - Zero ceremony, maximum beauty."""

import asyncio
from typing import Any, Dict, List

from resilient_result import Result

from cogency.constants import DEFAULT_MAX_ITERATIONS, MAX_FAILURES_HISTORY, MAX_ITERATIONS_HISTORY
from cogency.context import Context


class State(dict):
    """LangGraph-native state with zero ceremony.

    Pure dict for framework compatibility + dot notation for ergonomics.
    All behavior unified, no abstraction penalty.
    """

    def __init__(self, context: Context, query: str, **kwargs):
        super().__init__(
            {
                # Core immutable
                "context": context,
                "query": query,
                # Flow control
                "iteration": 0,
                "max_iterations": DEFAULT_MAX_ITERATIONS,
                "react_mode": "fast",
                "stop_reason": None,
                # Tool execution
                "selected_tools": [], # @preprocess
                "tool_calls": [], # @reason
                "result": Result,
                # Two-layer state architecture
                "actions": [],  # Complete ReAct cycles with rich records  
                "attempts": [],  # Compressed context for LLM prompting
                # Output
                "response": None,
                "verbose": kwargs.get("verbose", False),
                "trace": kwargs.get("trace", False),
                "callback": kwargs.get("callback"),
                **{k: v for k, v in kwargs.items() if k not in ["verbose", "trace", "callback"]},
            }
        )

    def __getattr__(self, name: str) -> Any:
        """Dot notation access to dict keys."""
        try:
            return self[name]
        except KeyError as err:
            raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'") from err

    def __setattr__(self, name: str, value: Any) -> None:
        """Dot notation assignment to dict keys."""
        self[name] = value

    def add_action(
        self,
        mode: str,
        thinking: str,
        planning: str,
        reflection: str,
        approach: str,
        tool_calls: List[Any],
    ) -> None:
        """Add action to reasoning history with new schema."""
        from datetime import datetime
        
        self.current_approach = approach

        action_entry = {
            "iteration": self.iteration,
            "timestamp": datetime.now().isoformat(),
            "mode": mode,
            "thinking": thinking,
            "planning": planning,
            "reflection": reflection,
            "approach": approach,
            "tool_calls": tool_calls,  # Tool execution results
            # Phase 2 compression fields (empty for now)
            "synthesis": "",
            "progress": "",
            "hypothesis": {"belief": "", "test": ""},
        }
        self.actions.append(action_entry)

        # Enforce history limit
        if len(self.actions) > MAX_ITERATIONS_HISTORY:
            self.actions = self.actions[-MAX_ITERATIONS_HISTORY:]

    def track_failure(self, tool_calls: List[Any], quality: str) -> None:
        """Track failed tool attempts."""
        failure_entry = {
            "tool_calls": tool_calls,
            "quality": quality,
            "iteration": self.iteration,
        }
        self.attempts.append(failure_entry)

        # Enforce failure history limit
        if len(self.attempts) > MAX_FAILURES_HISTORY:
            self.attempts = self.attempts[-MAX_FAILURES_HISTORY:]

    # Output behavior (formerly Output class)
    async def notify(self, event_type: str, data: Any) -> None:
        """Notify user of reasoning progress."""
        if self.callback and self.verbose and callable(self.callback):
            if asyncio.iscoroutinefunction(self.callback):
                await self.callback(str(data))
            else:
                self.callback(str(data))

# Function to compress actions into attempts for LLM prompting
def compress_actions(actions: List[Dict[str, Any]]) -> List[str]:
    """Phase 1: Basic compression of actions to readable format."""
    compressed = []
    for action in actions:
        for call in action.get("tool_calls", []):
            tool = call.get("tool", "unknown")
            outcome = call.get("outcome", "unknown") 
            params = call.get("params", {})
            # Simple readable format for Phase 1
            params_summary = str(params)[:50] + "..." if len(str(params)) > 50 else str(params)
            compressed.append(f"{tool}({params_summary}) → {outcome}")
    return compressed
