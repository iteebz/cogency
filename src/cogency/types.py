"""Pure type definitions for Cogency - TYPES ONLY."""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, TypedDict, Literal, Union
from pydantic import BaseModel, Field

from cogency.context import Context


# Output modes: "summary", "trace", "dev", "explain"
OutputMode = Literal["summary", "trace", "dev", "explain"]


# === AGENT STATE TYPES ===

class AgentState(TypedDict, total=False):
    # Core state
    context: Context
    trace: Optional[Any]  # ExecutionTrace - avoiding circular import
    query: str
    last_node_output: Optional[Any]
    
    # Routing and flow control
    next_node: Optional[str]
    direct_response: Optional[str]
    
    # Tool execution
    selected_tools: Optional[List[Any]]  # List[BaseTool]
    tool_calls: Optional[Any]
    execution_results: Optional[List[Dict[str, Any]]]
    
    # Reasoning
    reasoning_response: Optional[str]
    reasoning_decision: Optional[Any]  # ReasoningDecision
    can_answer_directly: Optional[bool]
    complexity_score: Optional[float]
    
    # Adaptive control
    adaptive_controller: Optional[Any]  # AdaptiveController
    
    # Final response
    final_response: Optional[str]


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