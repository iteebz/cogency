"""Execution tracing system - core component."""
import time
import asyncio
from functools import wraps
from copy import deepcopy
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cogency.types import OutputMode


class ExecutionTrace:
    """Dev-focused trace engine - stores execution details for debugging."""
    def __init__(self):
        self.entries = []

    def add(self, node: str, message: str, data: dict = None, explanation: str = None):
        """Add trace entry - DEV/DEBUG ONLY, no user streaming."""
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
        new_trace = ExecutionTrace()
        new_trace.entries = deepcopy(self.entries, memo)
        return new_trace


def _safe_deepcopy(obj):
    """Safe deepcopy that handles unpicklable objects."""
    try:
        return deepcopy(obj)
    except (TypeError, AttributeError):
        # Handle unpicklable objects like SimpleQueue
        if hasattr(obj, '__dict__'):
            safe_dict = {}
            for k, v in obj.__dict__.items():
                try:
                    safe_dict[k] = deepcopy(v)
                except (TypeError, AttributeError):
                    safe_dict[k] = f"<unpicklable: {type(v).__name__}>"
            return safe_dict
        else:
            return f"<unpicklable: {type(obj).__name__}>"


def trace_node(node_name: str):
    """Decorator that adds tracing via post-hoc state diff analysis."""
    def decorator(fn):
        @wraps(fn)
        async def wrapped(state, *args, **kwargs):
            # Take safe snapshot before execution
            before = _safe_deepcopy(state)
            
            # Execute pure business logic
            result = await fn(state, *args, **kwargs)
            
            # Take safe snapshot after execution
            after = _safe_deepcopy(result)
            
            # Compute diff and generate trace message
            delta = _compute_diff(before, after)
            message = _generate_trace_message(node_name, delta)
            
            # Add to trace if present
            if state.get("trace"):
                state["trace"].add(node_name, message, delta)
            
            return result
        return wrapped
    return decorator


def _compute_diff(before: dict, after: any) -> dict:
    """Compute meaningful differences between states."""
    diff = {}
    
    if not isinstance(after, dict):
        diff["result"] = after
        return diff
    
    if not isinstance(before, dict):
        diff["state_change"] = after
        return diff
    
    # Check for selected_tools changes
    if before.get("selected_tools") != after.get("selected_tools"):
        diff["selected_tools"] = after.get("selected_tools", [])
    
    # Check for context message changes
    before_context = before.get("context")
    after_context = after.get("context")
    
    if before_context and after_context:
        before_msgs = len(before_context.messages) if hasattr(before_context, 'messages') else 0
        after_msgs = len(after_context.messages) if hasattr(after_context, 'messages') else 0
        
        if before_msgs != after_msgs:
            diff["new_messages"] = after_msgs - before_msgs
            if after_msgs > 0 and hasattr(after_context, 'messages'):
                diff["latest_message"] = after_context.messages[-1]
    
    # Check for new keys in result
    for key in after:
        if key not in before and key not in ["context", "trace"]:
            diff[key] = after[key]
    
    return diff


def _generate_trace_message(node: str, delta: dict) -> str:
    """Generate meaningful trace message from state diff."""
    if node == "preprocess":
        if "selected_tools" in delta:
            tools = delta["selected_tools"]
            if tools:
                tool_names = [t.name for t in tools]
                return f"Selected {len(tools)} tools: {', '.join(tool_names)}"
            else:
                return "No tools selected"
        return "Completed preprocessing"
    
    elif node == "reason":
        if "new_messages" in delta:
            return f"Generated reasoning with {delta['new_messages']} new messages"
        return "Completed reasoning"
    
    elif node == "act":
        if "new_messages" in delta:
            return f"Executed tools with {delta['new_messages']} results"
        return "Executed tools"
    
    elif node == "respond":
        if "response" in delta:
            response = delta["response"]
            word_count = len(response.split())
            return f"Generated {word_count}-word response"
        return "Generated response"
    
    return f"Completed {node}"


# Alias for backward compatibility
trace = trace_node


# === TRACE PRESENTATION ===

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


def output_trace(trace: ExecutionTrace, mode: 'OutputMode'):
    """Output trace based on mode."""
    if mode == "summary":
        print(f"✅ {summarize_trace(trace)}")
    elif mode == "trace":
        print(format_trace(trace))
        print(f"\n✅ Complete")
    elif mode == "explain":
        print(format_trace(trace))  # Can be enhanced with explanations later
        print(f"\n✅ Complete")
    elif mode == "dev":
        print(format_full_debug(trace))
        print(f"\n✅ Complete")