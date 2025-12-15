from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Literal, Protocol, TypedDict, runtime_checkable


class UserEvent(TypedDict):
    type: Literal["user"]
    content: str
    timestamp: float


class ThinkEvent(TypedDict):
    type: Literal["think"]
    content: str
    timestamp: float


class CallEvent(TypedDict):
    type: Literal["call"]
    content: str
    timestamp: float


class ExecuteEvent(TypedDict):
    type: Literal["execute"]
    timestamp: float


class ResultEvent(TypedDict):
    type: Literal["result"]
    content: str
    timestamp: float
    payload: dict[str, Any] | None


class RespondEvent(TypedDict):
    type: Literal["respond"]
    content: str
    timestamp: float


class EndEvent(TypedDict):
    type: Literal["end"]
    timestamp: float


class MetricEvent(TypedDict):
    type: Literal["metric"]
    step: dict[str, Any]
    total: dict[str, Any]
    timestamp: float


class ErrorEvent(TypedDict):
    type: Literal["error"]
    content: str
    timestamp: float


class InterruptEvent(TypedDict):
    type: Literal["interrupt"]
    timestamp: float


class CancelledEvent(TypedDict):
    type: Literal["cancelled"]
    timestamp: float


Event = (
    UserEvent
    | ThinkEvent
    | CallEvent
    | ExecuteEvent
    | ResultEvent
    | RespondEvent
    | EndEvent
    | MetricEvent
    | ErrorEvent
    | InterruptEvent
    | CancelledEvent
)

EventType = Literal[
    "user",
    "think",
    "call",
    "execute",
    "result",
    "respond",
    "end",
    "metric",
    "error",
    "interrupt",
    "cancelled",
]

_CONTROL_EVENT_TYPES: set[EventType] = {"execute", "end", "interrupt"}


def event_type(event: Event) -> EventType:
    """Return the canonical type for an event."""

    return event["type"]


def event_content(event: Event) -> str:
    """Extract content from events that have it, empty string otherwise.

    Events with content: user, think, call, result, respond, error.
    Events without: execute, end, metric, interrupt, cancelled.
    """
    if "content" in event:
        return event["content"] or ""
    return ""


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


@dataclass
class ToolResult:
    """Tool execution result - pure data."""

    outcome: str  # Natural language completion: "Found 12 search results"
    content: str | None = None  # Optional detailed data for LLM context
    error: bool = False  # True if tool execution failed


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
    def stream(self, messages: list[dict]) -> AsyncGenerator[str, None]:
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

    def send(self, content: str) -> AsyncGenerator[str, None]:
        """Send message in session and stream response until turn completion.

        Only works after connect(). Session maintains conversation context.

        Args:
            content: User message for this turn

        Yields:
            Provider-native chunks until turn complete

        Turn completion is dual-channel:
        1. LLM semantic markers (execute, end events)
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
        self,
        conversation_id: str,
        user_id: str,
        type: str,
        content: str,
        timestamp: float | None = None,
    ) -> str:
        """Save single message to conversation. Returns message_id. Raises on failure."""
        ...

    async def load_messages(
        self,
        conversation_id: str,
        user_id: str,
        include: list[str] | None = None,
        exclude: list[str] | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        """Load conversation messages with optional type filtering and limit."""
        ...

    async def save_event(
        self, conversation_id: str, type: str, content: str, timestamp: float | None = None
    ) -> str:
        """Save runtime event for telemetry. Returns event_id. Raises on failure."""
        ...

    async def save_request(
        self,
        conversation_id: str,
        user_id: str,
        messages: str,
        response: str | None = None,
        timestamp: float | None = None,
    ) -> str:
        """Save LLM request/response for observability. Returns request_id. Raises on failure."""
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

    async def load_user_messages(
        self, user_id: str, since_timestamp: float = 0, limit: int | None = None
    ) -> list[str]:
        """Load user messages since timestamp for profile learning."""
        ...


@dataclass
class ToolParam:
    """Metadata for tool parameters."""

    description: str
    ge: int | float | None = None
    le: int | float | None = None
    min_length: int | None = None
    max_length: int | None = None


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


NotificationSource = Callable[[], Awaitable[list[str]]]
"""Source for system notifications injected between iterations."""
