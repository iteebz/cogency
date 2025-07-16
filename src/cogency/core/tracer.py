"""Trace formatting and output for clean separation of concerns."""
import time
from typing import List

from cogency.common.types import ExecutionTrace, OutputMode
from cogency.utils.explanation import ExplanationGenerator, ExplanationLevel, ExplanationContext, create_actionable_insights


class Tracer:
    """Handles formatting and output of execution traces."""

    def __init__(self, trace: ExecutionTrace):
        self.trace = trace
        self.explainer = ExplanationGenerator(ExplanationLevel.CONCISE)

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
        icons = {"think": "🤔", "plan": "🧠", "act": "⚡", "reflect": "🔍", "respond": "💬", "reason": "⚡", "memorize": "🧠", "select_tools": "🔧"}
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
    
    def _build_explanation_context(self) -> ExplanationContext:
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
                    import re
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
    
    def _generate_explanation_for_entry(self, entry: dict, context: ExplanationContext) -> str:
        """Generate explanation for a single trace entry."""
        node = entry["node"]
        message = entry["message"]
        data = entry.get("data", {})
        
        # Node-specific explanations
        if node == "memorize":
            if "recalled" in message.lower():
                return self.explainer.explain_memory_action("recall", message)
            else:
                return self.explainer.explain_memory_action("memorize", message)
        
        elif node == "select_tools":
            if "selected_tools" in data:
                tools = [tool.get("name", "unknown") for tool in data["selected_tools"]]
                return self.explainer.explain_tool_selection(tools, len(context.tools_available))
            else:
                return "🔧 Analyzing available tools for this task"
        
        elif node == "reason":
            if "Adaptive reasoning started" in message:
                return self.explainer.explain_reasoning_start(context)
            elif "Direct response" in message:
                return self.explainer.explain_reasoning_decision("direct_response", message)
            elif "Tool calls identified" in message:
                return self.explainer.explain_reasoning_decision("tool_needed", message)
            elif "Task complete" in message:
                return self.explainer.explain_reasoning_decision("task_complete", message)
            elif "Stopping" in message or "stopping" in message.lower():
                return self.explainer.explain_stopping_criteria(context.stopping_reason or "unknown", {"total_time": context.execution_time})
            elif "Tool execution" in message:
                return f"⚡ Executed tools and gathered information"
            else:
                return f"🤔 {message}"
        
        # Default fallback
        return None
    
    def _show_actionable_insights(self):
        """Show actionable insights based on trace analysis."""
        context = self._build_explanation_context()
        insights = create_actionable_insights(self.trace.entries, context)
        
        if insights:
            print("\n💡 Insights:")
            for insight in insights:
                print(f"   {insight}")

