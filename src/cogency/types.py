from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict, Literal
import time

from cogency.context import Context


# Output modes: "summary", "trace", "dev", "explain"
OutputMode = Literal["summary", "trace", "dev", "explain"]


@dataclass
class ReasoningDecision:
    """Structured decision from reasoning - NO JSON CEREMONY."""
    should_respond: bool
    response_text: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    task_complete: bool = False


class ExecutionTrace:
    """Lean trace engine - just stores entries with serialization safety."""
    def __init__(self):
        self.entries = []
        self._streaming_executor = None  # Set by StreamingExecutor when streaming

    def add(self, node: str, message: str, data: dict = None, explanation: str = None):
        # Ensure data is serializable by converting to basic types
        safe_data = self._make_serializable(data or {})
        timestamp = time.time()
        
        entry = {
            "node": node,
            "message": message,
            "data": safe_data,
            "explanation": explanation,
            "timestamp": timestamp
        }
        self.entries.append(entry)
        
        # Emit streaming event if streaming is active
        if self._streaming_executor and hasattr(self._streaming_executor, 'emit_trace_update'):
            # Create a task to emit the update (don't block trace.add)
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self._streaming_executor.emit_trace_update(
                        node, message, safe_data, timestamp
                    ))
            except RuntimeError:
                # No event loop, skip streaming
                pass
    
    def _make_serializable(self, obj):
        """Convert object to serializable form."""
        if obj is None:
            return None
        elif isinstance(obj, (str, int, float, bool)):
            return obj
        elif isinstance(obj, (list, tuple)):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        else:
            # For complex objects, store type name
            return f"<{type(obj).__name__}>"
    
    def __deepcopy__(self, memo):
        """Custom deepcopy to handle serialization."""
        from copy import deepcopy
        new_trace = ExecutionTrace()
        new_trace.entries = deepcopy(self.entries, memo)
        return new_trace


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