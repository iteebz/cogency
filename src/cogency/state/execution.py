"""ExecutionState - Pure execution tracking with zero ceremony."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from resilient_result import unwrap


class AgentMode(Enum):
    """Agent execution modes with clear semantics."""

    FAST = "fast"
    DEEP = "deep"
    ADAPT = "adapt"


class ExecutionState:
    """Execution tracking with persistent state."""

    def __init__(self, query: str, user_id: str = "default", store=None, state=None):
        # Core Identity
        self.query = query
        self.user_id = user_id

        # Always have persistence - default to SQLite
        if store is None:
            from cogency.persist.store import get_store

            store = get_store()
        self.store = store
        self.state = state

        # Loop Control
        self.iteration = 0
        self.max_iterations = 10
        self.mode = AgentMode.ADAPT
        self.stop_reason = None

        # Communication
        self.messages = []
        self.response = None

        # Tool Execution
        self.pending_calls = []
        self.completed_calls = []
        self.tool_results = {}
        self.iterations_without_tools = 0

        # System
        self.debug = False
        self.notifications = []

        # Security
        self.security_assessment = None

    def add_message(self, role: str, content: str) -> None:
        """Add to conversation history with immediate persistence."""
        self.messages.append(
            {"role": role, "content": content, "timestamp": datetime.now().isoformat()}
        )
        if self.state:
            self.state.persist()

    def set_tool_calls(self, calls: List[Dict[str, Any]]) -> None:
        """Set pending tool calls from reasoning with validation."""
        # Validate tool call structure before setting
        validated_calls = []
        for call in calls:
            validated_call = self._validate_tool_call(call)
            if validated_call:
                validated_calls.append(validated_call)

        self.pending_calls = validated_calls

    def _validate_tool_call(self, call: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validate and normalize tool call JSON structure."""
        if not isinstance(call, dict):
            return None

        # Required fields
        if "name" not in call:
            return None

        # Ensure args exists and is a dict
        if "args" not in call:
            call["args"] = {}
        elif not isinstance(call["args"], dict):
            return None

        # Basic tool call structure validation
        validated = {"name": str(call["name"]), "args": call["args"]}

        if "id" in call:
            validated["id"] = call["id"]

        return validated

    def finish_tools(self, results: List[Dict[str, Any]]) -> None:
        """Process completed tool results with immediate persistence."""
        self.completed_calls.extend(results)
        self.pending_calls.clear()
        self.iterations_without_tools = 0  # Reset counter on tool usage
        if self.state:
            self.state.persist()

        # Add tool results to conversation history so agent can see what was executed
        if results:
            tool_summary = []
            for result in results:
                tool_name = result.get("name", "unknown")
                result_obj = result.get("result")

                # Handle case where result_obj might be None (shouldn't happen but defensive)
                if result_obj is None:
                    tool_summary.append(f"Tool '{tool_name}' failed: No result returned")
                    continue

                try:
                    # Unwrap Result objects from resilient_result
                    unwrapped_result = unwrap(result_obj)

                    # For shell tools, show command output
                    if isinstance(unwrapped_result, dict) and "stdout" in unwrapped_result:
                        output = unwrapped_result["stdout"].strip()
                        if output:
                            tool_summary.append(
                                f"Tool '{tool_name}' executed successfully: {output}"
                            )
                        else:
                            tool_summary.append(
                                f"Tool '{tool_name}' executed successfully (no output)"
                            )
                    else:
                        # Generic success message
                        tool_summary.append(f"Tool '{tool_name}' executed successfully")

                except Exception as e:
                    # If unwrap fails, it means the Result was a failure
                    error_msg = str(e) if str(e) else "Unknown error"
                    tool_summary.append(f"Tool '{tool_name}' failed: {error_msg}")

            if tool_summary:
                self.add_message("system", "Tool execution results:\n" + "\n".join(tool_summary))

    def should_continue(self) -> bool:
        """Determine if reasoning loop should continue."""
        return (
            self.iteration < self.max_iterations
            and not self.response
            and not self.stop_reason
            and bool(self.pending_calls)
        )

    def advance_iteration(self) -> None:
        """Move to next reasoning iteration."""
        self.iteration += 1
        if self.state:
            self.state.persist()
