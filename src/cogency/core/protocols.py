"""Core protocols for provider abstraction."""

import json
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable



@dataclass
class ToolCall:
    """Tool call - structured input."""

    name: str
    args: dict[str, Any]

    @classmethod
    def from_json(cls, json_str: str) -> "ToolCall":
        """Parse ToolCall from JSON string."""
        data = json.loads(json_str)
        return cls(name=data["name"], args=data.get("args", {}))

    def to_json(self) -> str:
        """Serialize ToolCall to JSON string."""
        return json.dumps({"name": self.name, "args": self.args})


@dataclass
class ToolResult:
    """Tool execution result - pure data."""

    outcome: str  # Natural language completion: "Found 12 search results"
    content: str | None = None  # Optional detailed data for LLM context


@runtime_checkable
class LLM(Protocol):
    """LLM provider interface with clean layer separation.

    Infrastructure layer: Connection setup/teardown (raises on failure)
    Data layer: Pure token streaming (raises on failure)
    """

    # INFRASTRUCTURE LAYER - Direct exceptions for setup/config
    async def generate(self, messages: list[dict]) -> str: ...
    async def connect(self, messages: list[dict]) -> object: ...

    # DATA LAYER - Exception pattern for streaming
    async def stream(self, connection) -> AsyncGenerator[str, None]: ...

    # WebSocket session management (infrastructure)
    async def send(self, session, content: str) -> bool: ...
    async def receive(self, session) -> AsyncGenerator[str, None]: ...
    async def close(self, session) -> bool: ...


@runtime_checkable
class Storage(Protocol):
    """Storage protocol - honest failures, no silent lies."""

    async def save_message(
        self, conversation_id: str, user_id: str, type: str, content: str, timestamp: float = None
    ) -> None:
        """Save single message to conversation. Raises on failure."""
        ...

    async def load_messages(
        self, conversation_id: str, include: list[str] = None, exclude: list[str] = None
    ) -> list[dict]:
        """Load conversation messages with optional type filtering."""
        ...

    async def save_profile(self, user_id: str, profile: dict) -> None:
        """Save user profile. Raises on failure."""
        ...

    async def load_profile(self, user_id: str) -> dict:
        """Load latest user profile."""
        ...


class Tool(ABC):
    """Tool interface - clean attribute access."""

    # Class attributes - required
    name: str
    description: str
    schema: dict = {}
    examples: list[dict] = []

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute tool and return result. Handle errors internally."""
        pass
