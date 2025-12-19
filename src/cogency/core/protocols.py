from collections.abc import AsyncGenerator, Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Literal, NamedTuple, Protocol, TypedDict, cast, runtime_checkable


class MessageMatch(NamedTuple):
    """Past message match result."""

    content: str
    timestamp: float
    conversation_id: str


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
    return event["type"]


def event_content(event: Event) -> str:
    """Extract content or empty string. Content events: user, think, call, result, respond, error."""
    if "content" in event:
        return event["content"] or ""
    return ""


def is_control_event(event: Event) -> bool:
    return event_type(event) in _CONTROL_EVENT_TYPES


def is_execute(event: Event) -> bool:
    return event_type(event) == "execute"


def is_end(event: Event) -> bool:
    return event_type(event) == "end"


@runtime_checkable
class LLM(Protocol):
    """LLM interface: HTTP (stream/generate) and WebSocket (connect/send/close)."""

    def stream(self, messages: list[dict[str, Any]]) -> AsyncGenerator[str, None]: ...
    async def generate(self, messages: list[dict[str, Any]]) -> str: ...
    async def connect(self, messages: list[dict[str, Any]]) -> "LLM": ...
    def send(self, content: str) -> AsyncGenerator[str, None]: ...
    async def close(self) -> None: ...


@runtime_checkable
class Storage(Protocol):
    """Storage protocol. All methods raise on failure."""

    async def save_message(
        self,
        conversation_id: str,
        user_id: str,
        type: str,
        content: str,
        timestamp: float | None = None,
    ) -> str: ...
    async def load_messages(
        self,
        conversation_id: str,
        user_id: str,
        include: list[str] | None = None,
        exclude: list[str] | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]: ...
    async def save_event(
        self, conversation_id: str, type: str, content: str, timestamp: float | None = None
    ) -> str: ...
    async def save_request(
        self,
        conversation_id: str,
        user_id: str,
        messages: str,
        response: str | None = None,
        timestamp: float | None = None,
    ) -> str: ...
    async def save_profile(self, user_id: str, profile: dict[str, Any]) -> None: ...
    async def load_profile(self, user_id: str) -> dict[str, Any]: ...
    async def count_user_messages(self, user_id: str, since_timestamp: float = 0) -> int: ...
    async def load_user_messages(
        self, user_id: str, since_timestamp: float = 0, limit: int | None = None
    ) -> list[str]: ...
    async def delete_profile(self, user_id: str) -> int: ...
    async def load_latest_metric(self, conversation_id: str) -> dict[str, Any] | None: ...
    async def load_messages_by_conversation_id(
        self, conversation_id: str, limit: int
    ) -> list[dict[str, Any]]: ...
    async def search_messages(
        self, query: str, user_id: str, exclude_conversation_id: str | None, limit: int
    ) -> list[MessageMatch]: ...


@dataclass
class ToolCall:
    name: str
    args: dict[str, Any]


@dataclass
class ToolResult:
    outcome: str
    content: str | None = None
    error: bool = False


class ToolCallDict(TypedDict):
    """Wire format for tool calls at JSON boundaries."""

    name: str
    args: dict[str, Any]


class ToolResultDict(TypedDict, total=False):
    """Wire format for tool results at JSON boundaries."""

    outcome: str
    content: str


class ProfileDict(TypedDict, total=False):
    """Wire format for user profiles at JSON boundaries."""

    who: str
    style: str
    focus: str
    interests: str
    misc: str
    _meta: dict[str, Any]


class MetricDataDict(TypedDict, total=False):
    """Wire format for metric data at JSON boundaries."""

    step: dict[str, Any]
    total: dict[str, Any]


class ParseError(ValueError):
    """Raised when JSON parsing fails at a boundary."""

    def __init__(self, message: str, raw: object = None) -> None:
        super().__init__(message)
        self.raw = raw


def parse_tool_call_dict(raw: object, *, require_args: bool = False) -> ToolCallDict:
    """Parse raw JSON into ToolCallDict. Raises ParseError on invalid shape."""
    if not isinstance(raw, dict):
        raise ParseError(f"Expected dict, got {type(raw).__name__}", raw)
    data = cast("dict[str, Any]", raw)  # JSON boundary cast
    name = data.get("name")
    if not isinstance(name, str):
        raise ParseError(f"Field 'name' must be str, got {type(name).__name__}", data)

    if require_args and "args" not in data:
        raise ParseError("Field 'args' is required", data)

    args = data.get("args", {})
    if not isinstance(args, dict):
        raise ParseError(f"Field 'args' must be dict, got {type(args).__name__}", data)
    return {"name": name, "args": args}


def parse_tool_result_dict(raw: object) -> ToolResultDict:
    """Parse raw JSON into ToolResultDict. Raises ParseError on invalid shape."""
    if not isinstance(raw, dict):
        raise ParseError(f"Expected dict, got {type(raw).__name__}", raw)
    data = cast("dict[str, Any]", raw)  # JSON boundary cast
    result: ToolResultDict = {}
    outcome = data.get("outcome")
    if outcome is not None:
        if not isinstance(outcome, str):
            raise ParseError(f"Field 'outcome' must be str, got {type(outcome).__name__}", data)
        result["outcome"] = outcome
    content = data.get("content")
    if content is not None:
        if not isinstance(content, str):
            raise ParseError(f"Field 'content' must be str, got {type(content).__name__}", data)
        result["content"] = content
    return result


def parse_profile_dict(raw: object) -> ProfileDict:
    """Parse raw JSON into ProfileDict. Raises ParseError on invalid shape."""
    if not isinstance(raw, dict):
        raise ParseError(f"Expected dict, got {type(raw).__name__}", raw)
    data = cast("dict[str, Any]", raw)  # JSON boundary cast
    result: ProfileDict = {}
    for key in ("who", "style", "focus", "interests", "misc"):
        val = data.get(key)
        if val is not None:
            if not isinstance(val, str):
                raise ParseError(f"Field '{key}' must be str, got {type(val).__name__}", data)
            result[key] = val
    meta = data.get("_meta")
    if meta is not None:
        if not isinstance(meta, dict):
            raise ParseError(f"Field '_meta' must be dict, got {type(meta).__name__}", data)
        result["_meta"] = meta
    return result


def parse_metric_data_dict(raw: object) -> MetricDataDict:
    """Parse raw JSON into MetricDataDict. Raises ParseError on invalid shape."""
    if not isinstance(raw, dict):
        raise ParseError(f"Expected dict, got {type(raw).__name__}", raw)
    data = cast("dict[str, Any]", raw)  # JSON boundary cast
    result: MetricDataDict = {}
    step = data.get("step")
    if step is not None:
        if not isinstance(step, dict):
            raise ParseError(f"Field 'step' must be dict, got {type(step).__name__}", data)
        result["step"] = step
    total = data.get("total")
    if total is not None:
        if not isinstance(total, dict):
            raise ParseError(f"Field 'total' must be dict, got {type(total).__name__}", data)
        result["total"] = total
    return result


@dataclass
class ToolParam:
    description: str
    ge: int | float | None = None
    le: int | float | None = None
    min_length: int | None = None
    max_length: int | None = None


@runtime_checkable
class Tool(Protocol):
    name: str
    description: str
    schema: dict[str, Any]

    async def execute(self, **kwargs: Any) -> ToolResult: ...
    def describe(self, args: dict[str, Any]) -> str: ...


NotificationSource = Callable[[], Awaitable[list[str]]]
HistoryTransform = Callable[[list[dict[str, Any]]], Awaitable[list[dict[str, Any]]]]
