"""Core result types."""

import time


class AgentResult:
    """Agent execution result with conversation tracking."""

    def __init__(self, response: str, conversation_id: str = None):
        self.response = response
        self.conversation_id = conversation_id or f"conv_{int(time.time())}"

    def __str__(self) -> str:
        """Backward compatibility - returns response string."""
        return self.response or ""
