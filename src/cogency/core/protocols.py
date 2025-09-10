"""Core protocols for provider abstraction."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable

from .result import Result

# Unicode section symbol - zero collision risk with natural language
DELIMITER = "§"


@dataclass
class ToolResult:
    """Tool execution result - natural language outcome + optional content."""

    outcome: str  # Natural language completion: "File written to poison.txt"
    content: str | None = None  # Optional detailed data: file contents, search results, etc.

    def for_agent(self) -> str:
        """Format for agent consumption - outcome + content."""
        if self.content:
            return f"{self.outcome}\n\n{self.content}"
        return self.outcome

    def for_human(self) -> str:
        """Format for human display - just the natural language outcome."""
        return self.outcome


@dataclass
class WebSocketSession:
    """WebSocket session container - no more session['session'] bullshit."""

    session: object
    connection: object
    types: object


class Event(str, Enum):
    """Events - type-safe strings, no ceremony."""

    THINK = "think"
    CALLS = "calls"
    RESULTS = "results"
    RESPOND = "respond"
    USER = "user"
    YIELD = "yield"  # Control signal - not persisted, just execution handover

    @property
    def delimiter(self) -> str:
        """Convert event to streaming delimiter format."""
        return f"{DELIMITER}{self.upper()}"


class Mode(str, Enum):
    """Agent execution modes - type-safe strings, no ceremony."""

    RESUME = "resume"
    REPLAY = "replay"
    AUTO = "auto"

    def __eq__(self, other):
        if isinstance(other, str):
            return self.value == other
        return super().__eq__(other)

    def __hash__(self):
        return super().__hash__()


@runtime_checkable
class LLM(Protocol):
    """LLM provider interface with clean layer separation.

    Infrastructure layer (Results): Connection setup/teardown
    Data layer (Exceptions): Pure token streaming
    """

    # INFRASTRUCTURE LAYER - Results pattern for setup/config
    async def generate(self, messages: list[dict]) -> Result[str]: ...
    async def connect(self, messages: list[dict]) -> Result[object]: ...

    # DATA LAYER - Exception pattern for streaming
    async def stream(self, connection) -> AsyncGenerator[str, None]: ...

    # WebSocket session management (infrastructure)
    async def send(self, session, content: str) -> bool: ...
    async def receive(self, session) -> AsyncGenerator[str, None]: ...
    async def close(self, session) -> bool: ...


@runtime_checkable
class Storage(Protocol):
    """Storage protocol for conversation messages and user profiles."""

    async def save_message(
        self, conversation_id: str, user_id: str, type: str, content: str, timestamp: float = None
    ) -> bool:
        """Save single message to conversation."""
        ...

    async def load_messages(
        self, conversation_id: str, include: list[str] = None, exclude: list[str] = None
    ) -> list[dict]:
        """Load conversation messages with optional type filtering."""
        ...

    async def save_profile(self, user_id: str, profile: dict) -> bool:
        """Save user profile (with embedded metadata)."""
        ...

    async def load_profile(self, user_id: str) -> dict:
        """Load latest user profile."""
        ...


class Tool(ABC):
    """Tool interface with agent assistance capabilities."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    def schema(self) -> dict:
        return {}

    @property
    def examples(self) -> list[dict]:
        return []

    @abstractmethod
    async def execute(self, **kwargs) -> Result[ToolResult]:
        pass
