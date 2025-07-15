from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict, Literal
import time

from cogency.context import Context


# Output modes: "summary", "trace", "dev"
OutputMode = Literal["summary", "trace", "dev"]


@dataclass
class ReasoningDecision:
    """Structured decision from reasoning - NO JSON CEREMONY."""
    should_respond: bool
    response_text: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    task_complete: bool = False


class ExecutionTrace:
    """Lean trace engine - just stores entries."""
    def __init__(self):
        self.entries = []

    def add(self, node: str, message: str, data: dict = None):
        self.entries.append({
            "node": node,
            "message": message,
            "data": data or {},
            "timestamp": time.time()
        })


def summarize_trace(trace: ExecutionTrace) -> str:
    """Generate clean summary from trace entries."""
    summaries = []
    for entry in trace.entries:
        msg = entry["message"]
        if any(keyword in msg for keyword in ["Selected", "Executed", "Generated", "Completed"]):
            summaries.append(msg)
    
    if not summaries:
        return "Task completed"
    
    return " → ".join(summaries)


def format_trace(trace: ExecutionTrace) -> str:
    """Format full trace with icons."""
    icons = {"think": "🤔", "plan": "🧠", "act": "⚡", "reflect": "🔍", "respond": "💬", "reason": "⚡"}
    lines = []
    for entry in trace.entries:
        icon = icons.get(entry["node"], "📝")
        lines.append(f"   {icon} {entry['node'].upper():8} → {entry['message']}")
    return "\n".join(lines)


def format_full_debug(trace: ExecutionTrace) -> str:
    """Format full debug trace (dev mode)."""
    # For now, same as trace mode - can be extended later
    return format_trace(trace)


class AgentState(TypedDict):
    context: Context
    trace: Optional[ExecutionTrace]
    query: str
    last_node_output: Optional[Any]