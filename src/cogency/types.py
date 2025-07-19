"""Pure type definitions for Cogency - TYPES ONLY."""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, TypedDict, Literal, Union
from pydantic import BaseModel, Field

from cogency.context import Context


# Output modes: "summary", "trace", "dev", "explain"
OutputMode = Literal["summary", "trace", "dev", "explain"]


# === AGENT STATE TYPES ===

class AgentState(TypedDict):
    context: Context
    trace: Optional['ExecutionTrace']
    query: str
    last_node_output: Optional[Any]


@dataclass
class ReasoningDecision:
    """Structured decision from reasoning - NO JSON CEREMONY."""
    should_respond: bool
    response_text: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    task_complete: bool = False


# === TOOL TYPES ===

class ToolCall(BaseModel):
    name: str
    args: Dict[str, Any] = Field(default_factory=dict)


class MultiToolCall(BaseModel):
    calls: List[ToolCall]


class Plan(BaseModel):
    action: str
    answer: Optional[str] = None
    tool_call: Optional[Union[ToolCall, MultiToolCall]] = None