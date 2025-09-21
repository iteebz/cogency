"""Core protocols for provider abstraction."""

import json
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any, Literal, NotRequired, Protocol, TypedDict, runtime_checkable


class Event(TypedDict):
    type: Literal["think", "call", "result", "respond", "chunk", "metric", "execute", "end"]
    content: NotRequired[str]
    payload: NotRequired[dict[str, Any]]
    audience: NotRequired[Literal["broadcast", "internal", "observability"]]
    timestamp: NotRequired[float]


EventType = Literal[
    "think",
    "call",
    "result",
    "respond",
    "chunk",
    "metric",
    "execute",
    "end",
]

_CONTROL_EVENT_TYPES: set[EventType] = {"execute", "end"}


def event_type(event: Event) -> EventType:
    """Return the canonical type for an event."""

    return event["type"]


def event_content(event: Event) -> str:
    """Get the human-readable content payload if present."""

    return event.get("content", "") or ""


def is_control_event(event: Event) -> bool:
    """True when the event should stay inside parser/accumulator (execute/end)."""

    return event_type(event) in _CONTROL_EVENT_TYPES


def is_execute(event: Event) -> bool:
    return event_type(event) == "execute"


def is_end(event: Event) -> bool:
    return event_type(event) == "end"


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
    """Unified LLM interface supporting both HTTP streaming and WebSocket sessions.

    HTTP Pattern (stateless):
    - stream(messages) - Full conversation context each call
    - generate(messages) - One-shot completion

    WebSocket Pattern (stateful):
    - connect(messages) -> session LLM - Create session with initial context
    - send(content) - Send turn content, stream response (session only)
    - close() - Close session
    """

    # HTTP STREAMING - Stateless, full context each time
    async def stream(self, messages: list[dict]) -> AsyncGenerator[str, None]:
        """HTTP streaming with full conversation context.

        Args:
            messages: Complete conversation history

        Yields:
            Provider-native chunks until response complete
        """
        ...

    async def generate(self, messages: list[dict]) -> str:
        """One-shot completion with full conversation context.

        Args:
            messages: Complete conversation history

        Returns:
            Complete response string
        """
        ...

    # WEBSOCKET SESSIONS - Stateful, context preserved
    async def connect(self, messages: list[dict]) -> "LLM":
        """Create session with initial context. Returns session-enabled LLM.

        Args:
            messages: Initial conversation history for context

        Returns:
            Session-enabled LLM instance with preserved context
        """
        ...

    async def send(self, content: str) -> AsyncGenerator[str, None]:
        """Send message in session and stream response until turn completion.

        Only works after connect(). Session maintains conversation context.

        Args:
            content: User message for this turn

        Yields:
            Provider-native chunks until turn complete

        Turn completion is dual-channel:
        1. LLM semantic markers (§execute, §end)
        2. Provider infrastructure signals

        Provider-specific turn detection:
        - Gemini: requires both generation_complete AND turn_complete signals
        - OpenAI: response.done event
        """
        ...

    async def close(self) -> None:
        """Close session and cleanup resources. No-op for HTTP-only providers."""
        ...


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

    async def count_user_messages(self, user_id: str, since_timestamp: float = 0) -> int:
        """Count user messages since timestamp for learning cadence."""
        ...


class Tool(ABC):
    """Tool interface - clean attribute access."""

    # Class attributes - required
    name: str
    description: str
    schema: dict = {}

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute tool and return result. Handle errors internally."""
        pass

    @abstractmethod
    def describe(self, args: dict) -> str:
        """Human-readable action description for tool call."""
        pass
