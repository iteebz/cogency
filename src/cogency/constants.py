"""Centralized constants for cogency - eliminates magic strings."""

from enum import Enum


class ReasoningActions:
    """Action types for reasoning decisions."""
    RESPOND = "respond"
    USE_TOOL = "use_tool"
    USE_TOOLS = "use_tools"
    TOOL_NEEDED = "tool_needed"
    DIRECT_RESPONSE = "direct_response"


class NodeNames:
    """Workflow node identifiers."""
    REASON = "reason"
    ACT = "act"
    RESPOND = "respond"
    PREPROCESS = "preprocess"


class StatusValues:
    """Task/execution status values."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CONTINUE = "continue"
    COMPLETE = "complete"
    ERROR = "error"


class CalculatorOps:
    """Calculator operation types."""
    ADD = "add"
    SUBTRACT = "subtract"
    MULTIPLY = "multiply"
    DIVIDE = "divide"
    SQUARE_ROOT = "square_root"
    
    @classmethod
    def all(cls) -> list[str]:
        """Get all available operations."""
        return [cls.ADD, cls.SUBTRACT, cls.MULTIPLY, cls.DIVIDE, cls.SQUARE_ROOT]


class StateKeys:
    """Common state dictionary keys."""
    NEXT_NODE = "next_node"
    DIRECT_RESPONSE = "direct_response"
    TOOL_CALLS = "tool_calls"
    EXECUTION_RESULTS = "execution_results"
    CAN_ANSWER_DIRECTLY = "can_answer_directly"
    CONTEXT = "context"
    REASONING_RESPONSE = "reasoning_response"


class ResponseKeys:
    """Common response dictionary keys."""
    ERROR = "error"
    RESULT = "result"
    SUCCESS = "success"
    DATA = "data"
    MESSAGE = "message"


class EventTypes:
    """Streaming event types."""
    ERROR = "error"
    FINAL_STATE = "final_state"
    TRACE_UPDATE = "trace_update"
    NODE_START = "node_start"
    NODE_END = "node_end"