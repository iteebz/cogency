"""ExecutionState - Pure execution tracking with zero ceremony."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ExecutionState:
    """Pure execution tracking - minimal ceremony."""

    # Core Identity
    query: str
    user_id: str = "default"

    # Loop Control
    iteration: int = 0
    max_iterations: int = 10
    mode: str = "adapt"  # "fast" | "deep" | "adapt"
    stop_reason: Optional[str] = None

    # Communication
    messages: List[Dict[str, str]] = field(default_factory=list)
    response: Optional[str] = None

    # Tool Execution (Dictionary-based - Gemini's simplification)
    pending_calls: List[Dict[str, Any]] = field(default_factory=list)
    completed_calls: List[Dict[str, Any]] = field(default_factory=list)

    # System
    debug: bool = False
    notifications: List[Dict[str, Any]] = field(default_factory=list)

    def add_message(self, role: str, content: str) -> None:
        """Add to conversation history."""
        self.messages.append(
            {"role": role, "content": content, "timestamp": datetime.now().isoformat()}
        )

    def set_tool_calls(self, calls: List[Dict[str, Any]]) -> None:
        """Set pending tool calls from reasoning."""
        self.pending_calls = calls

    def complete_tool_calls(self, results: List[Dict[str, Any]]) -> None:
        """Process completed tool results."""
        self.completed_calls.extend(results)
        self.pending_calls.clear()

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
