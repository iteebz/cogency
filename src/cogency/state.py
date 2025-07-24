"""Cogency State container."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from cogency.context import Context
from cogency.output import Output


class Cognition:
    """Agent's cognitive state - memory, reasoning history, and action outcomes."""

    def __init__(self, react_mode: str = "fast", max_history: int = 5, max_failures: int = 5):
        self.react_mode = react_mode
        self.current_approach = "initial"
        self.action_fingerprints: List[Dict[str, str]] = []
        self.failed_attempts: List[Dict[str, Any]] = []
        self.last_tool_quality = "unknown"
        self.mode_switches: List[Dict[str, str]] = []
        self.max_history = max_history
        self.max_failures = max_failures

    def update(
        self,
        tool_calls: List[Any],
        current_approach: str,
        current_decision: str,
        action_fingerprint: str,
        formatted_result: str = "",
    ) -> None:
        """Update cognitive state with new action."""
        self.current_approach = current_approach

        action_entry = {
            "fingerprint": action_fingerprint,
            "result": formatted_result,
            "decision": current_decision,
        }
        self.action_fingerprints.append(action_entry)
        # Enforce history limit
        if len(self.action_fingerprints) > self.max_history:
            self.action_fingerprints = self.action_fingerprints[-self.max_history :]

    def update_result(self, formatted_result: str) -> None:
        """Update the last action's formatted result after execution."""
        if self.action_fingerprints:
            self.action_fingerprints[-1]["result"] = formatted_result

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
class NodeInput(BaseModel):
    """Base schema for node inputs."""

    iteration: int = 0
    max_iterations: int = 10
    context_data: Dict[str, Any] = Field(default_factory=dict)


class PreprocessInput(NodeInput):
    """Input schema for preprocess node."""

    query: str
    memory_enabled: bool = True


class ReasonInput(NodeInput):
    """Input schema for reason node."""

    selected_tools: List[Dict[str, Any]] = Field(default_factory=list)
    react_mode: str = "adaptive"  # fast, deep, adaptive
    cognition_state: Dict[str, Any] = Field(default_factory=dict)


class ActInput(NodeInput):
    """Input schema for act node."""

    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    selected_tools: List[Any] = Field(default_factory=list)


class RespondInput(NodeInput):
    """Input schema for respond node."""

    reasoning_response: Optional[str] = None
    can_answer_directly: bool = False
    direct_response: Optional[str] = None
    stopping_reason: Optional[str] = None


class NodeOutput(BaseModel):
    """Base schema for node outputs."""

    next_node: str
    success: bool = True
    errors: List[str] = Field(default_factory=list)


class PreprocessOutput(NodeOutput):
    """Output schema for preprocess node."""

    context_enriched: bool = False
    memories_retrieved: int = 0


class ReasonOutput(NodeOutput):
    """Output schema for reason node."""

    tool_calls: Optional[List[Dict[str, Any]]] = None
    reasoning_response: Optional[str] = None
    can_answer_directly: bool = False
    react_mode: str = "fast"
    stopping_reason: Optional[str] = None


class ActOutput(NodeOutput):
    """Output schema for act node."""

    execution_results: Dict[str, Any] = Field(default_factory=dict)
    successful_count: int = 0
    total_count: int = 0


class RespondOutput(NodeOutput):
    """Output schema for respond node."""

    final_response: str
    response_generated: bool = True


@dataclass
class State:
    """Agent state with dict-like access and schema validation."""

    # WORLD-CLASS MINIMALISM
    context: Context
    query: str
    output: Output = field(default_factory=Output)
    flow: Dict[str, Any] = field(default_factory=dict)  # Ephemeral workflow data
    cognition: Cognition = field(default_factory=lambda: Cognition())

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

    def validate_input(self, node_name: str) -> NodeInput:
        """Validate state data against node input schema."""
        schemas = {
            "preprocess": PreprocessInput,
            "reason": ReasonInput,
            "act": ActInput,
            "respond": RespondInput,
        }

        if node_name not in schemas:
            return NodeInput(**self.flow)

        # Extract relevant data for schema validation
        data = {
            "iteration": self.get("current_iteration", 0),
            "max_iterations": self.get("max_iterations", 10),
            "context_data": dict(self.flow),
        }

        # Add node-specific fields
        if node_name == "preprocess":
            data["query"] = self.query
            data["memory_enabled"] = True
        elif node_name == "reason":
            data["selected_tools"] = self.get("selected_tools", [])
            data["react_mode"] = self.get("react_mode", "adaptive")
            data["cognition_state"] = self.get("cognition", {})
        elif node_name == "act":
            data["tool_calls"] = self.get("tool_calls", [])
            data["selected_tools"] = self.get("selected_tools", [])
        elif node_name == "respond":
            data["reasoning_response"] = self.get("reasoning_response")
            data["can_answer_directly"] = self.get("can_answer_directly", False)
            data["direct_response"] = self.get("direct_response")
            data["stopping_reason"] = self.get("stopping_reason")

        return schemas[node_name](**data)
