"""Cogency State - Zero ceremony, maximum beauty."""

import asyncio
from typing import Any, Dict, List

from resilient_result import Result

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
                "max_iterations": 12,
                "react_mode": "fast",
                "stop_reason": None,
                # Tool execution
                "tool_calls": [],
                "selected_tools": [],
                "result": Result.ok({}),
                "execution_results": Result.ok({}),
                # Retry/failure tracking
                "tool_failures": 0,
                "quality_retries": 0,
                "tool_retries": 0,
                # Responses
                "reasoning": None,
                "response": None,
                "direct_answer": False,
                # Cognition data (flattened from old Cognition class)
                "iterations": [],  # Complete ReAct cycles
                "failed_attempts": [],  # Failed tool attempts
                "mode_switches": [],  # React mode changes
                "preserved_context": "",  # Context from truncated history
                "last_tool_quality": "unknown",
                "current_approach": "initial",
                # Output streaming (flattened from old Output class)
                "notifications": [],
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

    # Cognition behavior (formerly Cognition class)
    def update_cognition(
        self,
        tool_calls: List[Any],
        current_approach: str,
        current_decision: str,
        action_fingerprint: str,
        formatted_result: str = "",
    ) -> None:
        """Update cognitive state with new iteration."""
        self.current_approach = current_approach

        # Store complete iteration
        iteration_entry = {
            "iteration": self.iteration,
            "fingerprint": action_fingerprint,
            "tool_calls": tool_calls,
            "result": formatted_result,
            "decision": current_decision,
        }
        self.iterations.append(iteration_entry)

        # Enforce history limit with context preservation
        max_history = 5  # Reasonable default
        if len(self.iterations) > max_history:
            truncated = self.iterations[:-max_history]
            if truncated and not self.preserved_context:
                self.preserved_context = self._extract_cognitive_summary(truncated)
            self.iterations = self.iterations[-max_history:]

    def update_result(self, formatted_result: str) -> None:
        """Update the last iteration's result after execution."""
        if self.iterations:
            self.iterations[-1]["result"] = formatted_result

    def track_failure(self, tool_calls: List[Any], quality: str) -> None:
        """Track failed tool attempts."""
        failure_entry = {
            "tool_calls": tool_calls,
            "quality": quality,
            "iteration": self.iteration,
        }
        self.failed_attempts.append(failure_entry)

        # Enforce failure history limit
        max_failures = 5
        if len(self.failed_attempts) > max_failures:
            self.failed_attempts = self.failed_attempts[-max_failures:]

    def switch_mode(self, new_mode: str, reason: str) -> None:
        """Record mode switch with reason."""
        switch_entry = {
            "from": self.react_mode,
            "to": new_mode,
            "reason": reason,
        }
        self.mode_switches.append(switch_entry)
        self.react_mode = new_mode

    def _extract_cognitive_summary(self, truncated_iterations: List[Dict[str, Any]]) -> str:
        """Extract cognitive summary from iterations about to be truncated."""
        if not truncated_iterations:
            return ""

        decisions = []
        patterns = []

        for iteration in truncated_iterations:
            decision = iteration.get("decision", "")
            tool_calls = iteration.get("tool_calls", [])

            if decision:
                decisions.append(f"Iter {iteration.get('iteration', '?')}: {decision}")

            if tool_calls:
                tool_names = [call.get("name", "unknown") for call in tool_calls]
                patterns.append(f"Used: {', '.join(tool_names)}")

        summary_parts = []
        if decisions:
            summary_parts.append(f"Previous decisions: {'; '.join(decisions[-3:])}")
        if patterns:
            summary_parts.append(f"Tool patterns: {'; '.join(patterns[-3:])}")

        return " | ".join(summary_parts) if summary_parts else ""

    # Output behavior (formerly Output class)
    async def notify(self, event_type: str, data: Any) -> None:
        """Notify user of reasoning progress."""
        notification_entry = {"event_type": event_type, "data": data, "iteration": self.iteration}
        self.notifications.append(notification_entry)

        # Call the callback if available
        if self.callback and self.verbose and callable(self.callback):
            if asyncio.iscoroutinefunction(self.callback):
                await self.callback(str(data))
            else:
                self.callback(str(data))


def summarize_attempts(failed_attempts: List[Dict[str, Any]]) -> str:
    """Create a summary of previous failed attempts."""
    if not failed_attempts:
        return "No previous failed attempts"

    failure_summaries = []
    for attempt in failed_attempts[-3:]:  # Last 3 failures
        tool_calls = attempt.get("tool_calls", [])
        quality = attempt.get("quality", "unknown")

        if tool_calls:
            tool_names = [call.get("name", "unknown") for call in tool_calls]
            tools_str = ", ".join(tool_names)
            failure_summaries.append(f"{tools_str} ({quality})")
        else:
            failure_summaries.append(f"unknown tool ({quality})")

    return (
        f"Previous failed attempts: {len(failed_attempts)} attempts failed. "
        f"Last failures: {', '.join(failure_summaries)}"
    )
