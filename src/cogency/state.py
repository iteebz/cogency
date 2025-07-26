"""Cogency State container."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from cogency.context import Context
from cogency.output import Output
from cogency.utils.results import Result


class Cognition:
    """Agent's cognitive state - memory, reasoning history, and action outcomes."""

    def __init__(self, react_mode: str = "fast", max_history: int = 5, max_failures: int = 5):
        self.react_mode = react_mode
        self.current_approach = "initial"
        # Store complete iterations (ReAct cycles)
        self.iterations: List[Dict[str, Any]] = []
        self.failed_attempts: List[Dict[str, Any]] = []
        self.last_tool_quality = "unknown"
        self.mode_switches: List[Dict[str, str]] = []
        self.max_history = max_history  # Now limits iterations, not individual actions
        self.max_failures = max_failures
        # Preserve cognitive context across mode switches
        self.preserved_context: str = ""

    def update(
        self,
        tool_calls: List[Any],
        current_approach: str,
        current_decision: str,
        action_fingerprint: str,
        formatted_result: str = "",
        iteration: int = 0,
    ) -> None:
        """Update cognitive state with new iteration."""
        self.current_approach = current_approach

        # Store as iteration entry
        iteration_entry = {
            "iteration": iteration,
            "fingerprint": action_fingerprint,
            "tool_calls": tool_calls,
            "result": formatted_result,
            "decision": current_decision,
        }
        self.iterations.append(iteration_entry)

        # Enforce iteration limit with context preservation
        if len(self.iterations) > self.max_history:
            # Preserve context before truncation
            truncated_iterations = self.iterations[: -self.max_history]
            if truncated_iterations and not self.preserved_context:
                self.preserved_context = self._extract_cognitive_summary(truncated_iterations)
            self.iterations = self.iterations[-self.max_history :]

    def update_result(self, formatted_result: str) -> None:
        """Update the last iteration's formatted result after execution."""
        if self.iterations:
            self.iterations[-1]["result"] = formatted_result

    def track_failure(self, tool_calls: List[Any], quality: str, iteration: int) -> None:
        """Track failed tool attempts."""
        failure_entry = {
            "tool_calls": tool_calls,
            "quality": quality,
            "iteration": iteration,
        }
        self.failed_attempts.append(failure_entry)
        # Enforce failure history limit
        if len(self.failed_attempts) > self.max_failures:
            self.failed_attempts = self.failed_attempts[-self.max_failures :]

    def set_tool_quality(self, quality: str) -> None:
        """Set the quality assessment of the last tool execution."""
        self.last_tool_quality = quality

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

        # Extract key decisions and patterns from truncated iterations
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

    def get(self, key: str, default: Any = None) -> Any:
        """Dict-like access for backward compatibility."""
        return getattr(self, key, default)


def summarize_attempts(failed_attempts: List[Dict[str, Any]]) -> str:
    """Create a summary of previous failed attempts."""
    if not failed_attempts:
        return "No previous failed attempts"

    failure_summaries = []
    for attempt in failed_attempts[-3:]:  # Last 3 failures
        tool_calls = attempt.get("tool_calls", [])
        quality = attempt.get("quality", "unknown")

        if tool_calls:
            # Extract tool names from tool calls
            tool_names = [call.get("name", "unknown") for call in tool_calls]
            tools_str = ", ".join(tool_names)
            failure_summaries.append(f"{tools_str} ({quality})")
        else:
            failure_summaries.append(f"unknown tool ({quality})")

    return (
        f"Previous failed attempts: {len(failed_attempts)} attempts failed. "
        f"Last failures: {', '.join(failure_summaries)}"
    )


# Input/Output Schemas for Clear Data Flow


@dataclass
class State:
    """Agent state with dict-like access and schema validation."""

    # WORLD-CLASS MINIMALISM
    context: Context
    query: str
    output: Output = field(default_factory=Output)
    flow: Dict[str, Any] = field(default_factory=dict)  # Ephemeral workflow data
    cognition: Cognition = field(default_factory=lambda: Cognition())

    # Smart defaults - eliminate manual ceremony
    @property
    def tool_calls(self) -> List[Dict[str, Any]]:
        """Tool calls with intelligent default."""
        return self.flow.get("tool_calls", [])

    @property
    def selected_tools(self) -> List[Any]:
        """Selected tools with intelligent default."""
        return self.flow.get("selected_tools", [])

    @property
    def result(self) -> Result:
        """Result from act node."""
        return self.flow.get("result", Result.ok({}))

    @property
    def iteration(self) -> int:
        """Current iteration with intelligent default."""
        return self.flow.get("iteration", 0)

    @iteration.setter
    def iteration(self, value: int) -> None:
        """Set current iteration."""
        self.flow["iteration"] = value

    @property
    def max_iterations(self) -> int:
        """Max iterations with intelligent default."""
        return self.flow.get("MAX_ITERATIONS", 12)

    @property
    def stop_reason(self) -> Optional[str]:
        """Stopping reason with intelligent default."""
        return self.flow.get("stop_reason")

    @property
    def react_mode(self) -> str:
        """React mode with intelligent default."""
        return self.flow.get("react_mode", "fast")

    @react_mode.setter
    def react_mode(self, value: str) -> None:
        """Set react mode."""
        self.flow["react_mode"] = value

    @property
    def reasoning(self) -> Optional[str]:
        """Reasoning response with intelligent default."""
        return self.flow.get("reasoning")

    @property
    def response(self) -> Optional[str]:
        """Direct response with intelligent default."""
        return self.flow.get("response")

    @property
    def direct_answer(self) -> bool:
        """Can answer directly with intelligent default."""
        return self.flow.get("direct_answer", False)

    @property
    def tool_failures(self) -> int:
        """Failed tool attempts with intelligent default."""
        return self.flow.get("tool_failures", 0)

    @property
    def quality_retries(self) -> int:
        """Quality retry attempts with intelligent default."""
        return self.flow.get("quality_retries", 0)

    @property
    def tool_retries(self) -> int:
        """Network retry count with intelligent default."""
        return self.flow.get("tool_retries", 0)

    @property
    def execution_results(self) -> Any:
        """Execution results with intelligent default."""
        from cogency.utils.results import Result

        return self.flow.get("execution_results", Result.ok({}))

    def get(self, key: str, default: Any = None) -> Any:
        if key in self.flow:
            return self.flow[key]
        return getattr(self, key, default)

    def __contains__(self, key: str) -> bool:
        return key in self.flow or hasattr(self, key)

    def __getitem__(self, key: str) -> Any:
        """Dict-like access for backward compatibility."""
        if key in self.flow:
            return self.flow[key]
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(f"'{key}' not found in state")

    def __setitem__(self, key: str, value: Any) -> None:
        """Dict-like assignment for backward compatibility."""
        self.flow[key] = value

