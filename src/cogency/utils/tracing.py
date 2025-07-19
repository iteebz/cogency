"""Comprehensive tracing utilities for recording and reporting."""
from functools import wraps
from copy import deepcopy
from typing import Dict, Any, List, Optional
import time
import re

from cogency.utils.diff import compute_diff, generate_trace_message
from cogency.common.types import ExecutionTrace, OutputMode
# Lazy imports to avoid circular dependencies


def _safe_deepcopy(obj):
    """Safe deepcopy that handles unpicklable objects."""
    try:
        return deepcopy(obj)
    except (TypeError, AttributeError) as e:
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
            delta = compute_diff(before, after)
            message = generate_trace_message(node_name, delta)
            
            # Add to trace if present
            if state.get("trace"):
                state["trace"].add(node_name, message, delta)
            
            return result
        return wrapped
    return decorator


# Alias for backward compatibility
trace = trace_node


class Tracer:
    """Handles formatting and output of execution traces."""

    def __init__(self, trace: ExecutionTrace):
        self.trace = trace

    def _summarize(self) -> str:
        """Generate clean summary from trace entries."""
        summaries = []
        for entry in self.trace.entries:
            msg = entry["message"]
            if any(keyword in msg for keyword in ["Selected", "Executed", "Generated", "Completed"]):
                summaries.append(msg)
        
        if not summaries:
            return "Task completed"
        
        return " → ".join(summaries)

    def _format_trace(self) -> str:
        """Format full trace with icons."""
        icons = {"think": "🤔", "plan": "🧠", "act": "⚡", "reflect": "🔍", "respond": "💬", "reason": "⚡", "memorize": "🧠", "filter_tools": "🔧"}
        lines = []
        for entry in self.trace.entries:
            icon = icons.get(entry["node"], "📝")
            lines.append(f"   {icon} {entry['node'].upper():8} → {entry['message']}")
        return "\n".join(lines)
    
    def _format_explained_trace(self) -> str:
        """Format trace with human-readable explanations."""
        lines = []
        context = self._build_explanation_context()
        
        for entry in self.trace.entries:
            # Use existing explanation if available, otherwise generate one
            explanation = entry.get("explanation")
            if not explanation:
                explanation = self._generate_explanation_for_entry(entry, context)
            
            if explanation:
                lines.append(f"   {explanation}")
        
        return "\n".join(lines)

    def _format_full_debug(self) -> str:
        """Format full debug trace (dev mode)."""
        # For now, same as trace mode - can be extended later
        return self._format_trace()

    def output(self, mode: OutputMode):
        """Output trace based on mode."""
        if mode == "summary":
            print(f"✅ {self._summarize()}")
        elif mode == "trace":
            print(self._format_trace())
            print(f"\n✅ Complete")
        elif mode == "explain":
            print(self._format_explained_trace())
            self._show_actionable_insights()
            print(f"\n✅ Complete")
        elif mode == "dev":
            print(self._format_full_debug())
            print(f"\n✅ Complete")
    
    def _build_explanation_context(self):
        from cogency.react.explanation import ExplanationContext
        """Build context for explanation generation."""
        # Extract context from trace entries
        user_query = "Unknown query"
        tools_available = []
        reasoning_depth = 1
        execution_time = 0.0
        success = True
        stopping_reason = None
        
        if self.trace.entries:
            start_time = self.trace.entries[0]["timestamp"]
            end_time = self.trace.entries[-1]["timestamp"]
            execution_time = end_time - start_time
            
            for entry in self.trace.entries:
                message = entry.get("message", "")
                data = entry.get("data", {})
                
                # Extract query
                if "query" in data:
                    user_query = data["query"]
                
                # Extract tools
                if "selected_tools" in data:
                    tools_available = [tool.get("name", "unknown") for tool in data["selected_tools"]]
                
                # Extract reasoning depth
                if "max_iterations" in message:
                    match = re.search(r'max_iterations: (\d+)', message)
                    if match:
                        reasoning_depth = int(match.group(1))
                
                # Extract stopping reason
                if "Stopping" in message or "stopping" in message.lower():
                    stopping_reason = message.split(":")[-1].strip()
        
        return ExplanationContext(
            user_query=user_query,
            tools_available=tools_available,
            reasoning_depth=reasoning_depth,
            execution_time=execution_time,
            success=success,
            stopping_reason=stopping_reason
        )
    
    def _generate_explanation_for_entry(self, entry: dict, context: "ExplanationContext") -> str:
        """Generate explanation for a single trace entry."""
        node = entry["node"]
        message = entry["message"]
        data = entry.get("data", {})
        
        # Node-specific explanations
        if node == "memorize":
            if "recalled" in message.lower():
                return f"RECALL: {message}"
            else:
                return f"MEMORIZE: {message}"
        
        elif node == "filter_tools":
            if "selected_tools" in data:
                tools = [tool.get("name", "unknown") for tool in data["selected_tools"]]
                return f"TOOLING: {', '.join(tools) if tools else 'No tools needed'}"
            else:
                return "🔧 Analyzing available tools for this task"
        
        elif node == "reason":
            if "Adaptive reasoning started" in message:
                return "REASON: Starting reasoning process"
            elif "Direct response" in message:
                return f"REASON: {message}"
            elif "Tool calls identified" in message:
                return f"REASON: {message}"
            elif "Task complete" in message:
                return f"REASON: {message}"
            elif "Stopping" in message or "stopping" in message.lower():
                return f"COMPLETE: Task finished ({context.stopping_reason or 'unknown'})"
            elif "Tool execution" in message:
                return f"⚡ Executed tools and gathered information"
            else:
                return f"🤔 {message}"
        
        # Default fallback
        return None
    
    def _show_actionable_insights(self):
        from cogency.react.explanation import create_actionable_insights
        """Show actionable insights based on trace analysis."""
        context = self._build_explanation_context()
        insights = create_actionable_insights(self.trace.entries, context)
        
        if insights:
            print("\n💡 Insights:")
            for insight in insights:
                print(f"   {insight}")