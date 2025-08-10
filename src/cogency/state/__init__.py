"""Agent state management - Database-as-State architecture.

Pure data + pure functions = beautiful state management.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List
from uuid import uuid4

from .modes import AgentMode  # noqa: F401
from .state import State  # noqa: F401


@dataclass
class Profile:
    """Persistent user context across sessions."""

    user_id: str
    preferences: Dict[str, Any] = field(default_factory=dict)
    goals: List[str] = field(default_factory=list)
    expertise_areas: List[str] = field(default_factory=list)
    communication_style: str = ""
    projects: Dict[str, str] = field(default_factory=dict)
    interaction_count: int = 0  # LEGACY: For memory tests

    created_at: datetime = field(default=None)
    last_updated: datetime = field(default=None)

    def __post_init__(self):
        """Ensure both timestamps are set to same value on creation."""
        if self.created_at is None or self.last_updated is None:
            now = datetime.now()
            if self.created_at is None:
                self.created_at = now
            if self.last_updated is None:
                self.last_updated = now

    @property
    def expertise(self) -> List[str]:
        """Backward compatibility alias for expertise_areas."""
        return self.expertise_areas

    @expertise.setter
    def expertise(self, value: List[str]) -> None:
        """Backward compatibility setter for expertise_areas."""
        self.expertise_areas = value


@dataclass
class Workspace:
    """Ephemeral task state within sessions."""

    objective: str = ""
    assessment: str = ""
    approach: str = ""
    observations: List[str] = field(default_factory=list)
    insights: List[str] = field(default_factory=list)
    facts: Dict[str, Any] = field(default_factory=dict)
    thoughts: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class Conversation:
    """Persistent conversation history across tasks."""

    conversation_id: str = field(default_factory=lambda: str(uuid4()))
    user_id: str = ""
    messages: List[Dict[str, Any]] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class Execution:
    """Runtime-only execution mechanics - NOT persisted."""

    iteration: int = 0
    max_iterations: int = 10
    mode: str = "adapt"
    stop_reason: str | None = None

    messages: List[Dict[str, Any]] = field(default_factory=list)
    response: str | None = None

    pending_calls: List[Dict[str, Any]] = field(default_factory=list)
    completed_calls: List[Dict[str, Any]] = field(default_factory=list)
    iterations_without_tools: int = 0
    tool_results: Dict[str, Any] = field(default_factory=dict)


# Compatibility aliases
UserProfile = Profile
ExecutionState = Execution

__all__ = ["Profile", "Workspace", "Conversation", "Execution", "State", "AgentMode"]
