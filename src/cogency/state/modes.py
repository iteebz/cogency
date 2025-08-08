"""Agent execution modes."""

from enum import Enum


class AgentMode(Enum):
    """Agent reasoning modes."""

    ADAPT = "adapt"
    FAST = "fast"
    DEEP = "deep"

    def __str__(self) -> str:
        return self.value
