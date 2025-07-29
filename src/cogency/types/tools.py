"""Tool types with beautiful property wrapper pattern - zero ceremony."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class ToolOutcome(Enum):
    """Standardized tool execution results."""

    SUCCESS = "success"  # Tool executed successfully with expected output
    FAILURE = "failure"  # Tool executed but failed (e.g., file not found)
    ERROR = "error"  # Tool execution error (e.g., syntax error, crash)
    TIMEOUT = "timeout"  # Tool execution exceeded time limit


class ToolResult:
    """Beautiful property wrapper for tool execution results."""

    def __init__(self, data: Dict[str, Any]):
        self._data = data

    @property
    def name(self) -> str:
        return self._data.get("name", "unknown")

    @property
    def args(self) -> Dict[str, Any]:
        return self._data.get("args", {})

    @property
    def result(self) -> Optional[str]:
        return self._data.get("result")

    @property
    def outcome(self) -> str:
        return self._data.get("outcome", "unknown")

    @property
    def success(self) -> bool:
        """Clean success check."""
        return self.outcome == "success"

    def __repr__(self) -> str:
        return f"ToolResult(name={self.name}, outcome={self.outcome})"


@dataclass
class ToolCall:
    """Clean tool call structure for reasoning phase."""

    name: str
    args: Dict[str, Any]
    result: Optional[str] = None
    outcome: Optional[ToolOutcome] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for storage."""
        return {
            "name": self.name,
            "args": self.args,
            "result": self.result,
            "outcome": self.outcome.value if self.outcome else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolCall":
        """Create from dict storage."""
        outcome = None
        if data.get("outcome"):
            outcome = ToolOutcome(data["outcome"])

        return cls(
            name=data.get("name", ""),
            args=data.get("args", {}),
            result=data.get("result"),
            outcome=outcome,
        )
