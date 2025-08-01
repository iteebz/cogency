"""Cogency State - Zero ceremony, maximum beauty."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from resilient_result import Result


@dataclass
class State:
    """Clean dataclass state for agent execution."""

    # Core execution context
    query: str
    user_id: str = "default"
    messages: List[Dict[str, str]] = field(default_factory=list)
    # Flow control
    iteration: int = 0
    depth: int = 10
    mode: str = "fast"
    stop_reason: Optional[str] = None
    # Tool execution
    selected_tools: List[Any] = field(default_factory=list)
    tool_calls: List[Any] = field(default_factory=list)
    result: Any = None
    # Two-layer state architecture
    actions: List[Dict[str, Any]] = field(default_factory=list)
    attempts: List[Any] = field(default_factory=list)
    # Cognitive workspace - persistent semantic memory
    objective: str = ""
    assessment: str = ""
    approach: str = ""
    observations: str = ""
    # Output
    response: Optional[str] = None
    response_source: Optional[str] = None  # Track which phase generated response
    notify: bool = True
    debug: bool = False
    callback: Any = None
    notifications: List[Dict[str, Any]] = field(default_factory=list)

    def add_message(self, role: str, content: str) -> None:
        """Add message to conversation history."""
        self.messages.append({"role": role, "content": content})

    def conversation(self) -> List[Dict[str, str]]:
        """Get clean conversation for LLM."""
        return [{"role": msg["role"], "content": msg["content"]} for msg in self.messages]

    def add_action(
        self,
        mode: str,
        thinking: str,
        planning: str,
        reflection: str,
        approach: str,
        tool_calls: List[Dict[str, Any]],
    ) -> None:
        """Add action to reasoning history with new schema."""
        from datetime import datetime

        self.approach = approach

        action_entry = {
            "iteration": self.iteration,
            "timestamp": datetime.now().isoformat(),
            "mode": mode,
            "thinking": thinking,
            "planning": planning,
            "reflection": reflection,
            "approach": approach,
            "tool_calls": tool_calls,
            # NO compression fields - handled by situation_summary
        }
        self.actions.append(action_entry)

        # Enforce history limit
        if len(self.actions) > 5:
            self.actions = self.actions[-5:]

    def add_tool_result(
        self,
        name: str,
        args: dict,
        result: Result,
        iteration: Optional[int] = None,
    ) -> None:
        """Add tool execution result to current action (schema-compliant)."""
        if not self.actions:
            raise ValueError("Cannot add tool result without an active action")

        current_action = self.actions[-1]
        # Use unwrap to properly extract result data
        from resilient_result import unwrap

        stored_result = unwrap(result) if result.success else result.error

        tool_call = {
            "name": name,
            "args": args,
            "result": stored_result,
            "outcome": "success" if result.success else "failure",
            # NO compression fields - handled by situation_summary
        }

        # Initialize tool_calls if needed
        if "tool_calls" not in current_action:
            current_action["tool_calls"] = []

        current_action["tool_calls"].append(tool_call)

    def latest_results(self) -> List[Dict[str, Any]]:
        """Get tool results from most recent action as dicts."""
        if not self.actions:
            return []

        latest_action = self.actions[-1]
        # Filter for tool calls that have a non-None 'outcome' value, indicating they are executed results
        return [
            call for call in latest_action.get("tool_calls", []) if call.get("outcome") is not None
        ]

    @property
    def latest_tool_results(self) -> List[Dict[str, Any]]:
        """Beautiful property wrapper for latest tool results."""
        return self.latest_results()

    def update_workspace(self, workspace_update: dict) -> None:
        """Update cognitive workspace fields with minimal bounds checking."""
        for field_name, value in workspace_update.items():
            if (
                field_name in ["objective", "assessment", "approach", "observations"]
                and isinstance(value, str)
                and len(value.strip()) <= 500
            ):  # Reasonable bounds
                setattr(self, field_name, value.strip())

    def workspace_context(self) -> str:
        """Build workspace context string for reasoning."""
        parts = []
        if self.objective:
            parts.append(f"OBJECTIVE: {self.objective}")
        if self.assessment:
            parts.append(f"ASSESSMENT: {self.assessment}")
        if self.approach:
            parts.append(f"APPROACH: {self.approach}")
        if self.observations:
            parts.append(f"OBSERVATIONS: {self.observations}")
        return "\n".join(parts) if parts else "No workspace context yet"

    def reasoning_context(self, mode: str, max_history: int = 3) -> str:
        """Pure functional context generation using cognitive workspace."""
        workspace = self.workspace_context()

        # Latest tool results for immediate context
        latest_results = self.latest_results()
        latest_context = ""
        if latest_results:
            latest_parts = []
            for call in latest_results:
                name = call.get("name", "unknown")
                args = call.get("args", {})
                result_data = call.get("result", "")
                # Handle result being a dict or string
                if isinstance(result_data, dict) and "content" in result_data:
                    # Files tool result format
                    result_snippet = result_data["content"][:200]
                elif isinstance(result_data, dict) and "output" in result_data:
                    result_snippet = result_data["output"][:200]
                else:
                    result_snippet = str(result_data)[:200]
                latest_parts.append(f"✓ {name}({args}) executed: {result_snippet}")
            latest_context = "\n".join(latest_parts)

        if mode == "deep":
            context_parts = []
            if workspace != "No workspace context yet":
                context_parts.append(f"WORKSPACE:\n{workspace}")
            if latest_context:
                context_parts.append(f"LATEST RESULTS:\n{latest_context}")
            return "\n\n".join(context_parts) if context_parts else "No context available"
        else:
            # Fast mode: workspace + latest only
            if workspace != "No workspace context yet" and latest_context:
                return f"{workspace}\n\nLATEST: {latest_context}"
            elif workspace != "No workspace context yet":
                return workspace
            elif latest_context:
                return f"LATEST: {latest_context}"
            else:
                return "No context available"


# Export clean State class


# Function to compress actions into attempts for LLM prompting
def compress_actions(actions: List[Dict[str, Any]]) -> List[str]:
    """Phase 1: Basic compression of actions to readable format (schema-compliant)."""
    compressed = []
    for action in actions:
        for call in action.get("tool_calls", []):
            name = call.get("name", "unknown")
            args = call.get("args", {})
            outcome = call.get("outcome", "unknown")
            result_data = call.get("result", "")

            # Handle result being a dict or string
            if isinstance(result_data, dict) and "output" in result_data:
                result_snippet = result_data["output"][:50]
            else:
                result_snippet = str(result_data)[:50]

            # Format: tool(args) → outcome: result_snippet
            args_summary = str(args)[:20] + "..." if len(str(args)) > 20 else str(args)

            if result_snippet:
                compressed.append(f"{name}({args_summary}) → {outcome}: {result_snippet}")
            else:
                compressed.append(f"{name}({args_summary}) → {outcome}")

    return compressed
