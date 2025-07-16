"""Human-readable explanation generation for reasoning steps and tool usage."""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import re


class ExplanationLevel(Enum):
    """Different levels of explanation detail."""
    CONCISE = "concise"      # Brief, user-friendly
    DETAILED = "detailed"    # More context and reasoning
    TECHNICAL = "technical"  # Full technical details


@dataclass
class ExplanationContext:
    """Context for generating contextual explanations."""
    user_query: str
    tools_available: List[str]
    reasoning_depth: int
    execution_time: float
    success: bool
    stopping_reason: Optional[str] = None


class ExplanationGenerator:
    """Generates human-readable explanations for reasoning steps and tool usage."""
    
    def __init__(self, level: ExplanationLevel = ExplanationLevel.CONCISE):
        self.level = level
        self._tool_explanations = {
            "search": "searched for information",
            "file_read": "read file contents",
            "file_write": "saved information to file",
            "calculator": "performed calculations",
            "web_scraper": "retrieved web content",
            "database": "queried database",
            "api_call": "made API request",
            "email": "sent email",
            "recall": "retrieved relevant memories",
            "memorize": "saved important information"
        }
    
    def explain_reasoning_start(self, context: ExplanationContext) -> str:
        """Generate explanation for reasoning process initiation."""
        complexity_desc = self._describe_complexity(context.reasoning_depth)
        
        if self.level == ExplanationLevel.CONCISE:
            return f"🤔 Starting to think through your request ({complexity_desc})"
        elif self.level == ExplanationLevel.DETAILED:
            return f"🤔 Beginning reasoning process for: '{context.user_query}' with {complexity_desc} approach"
        else:
            return f"🤔 Initializing adaptive reasoning with max_iterations={context.reasoning_depth}, query_complexity={complexity_desc}"
    
    def explain_tool_selection(self, selected_tools: List[str], total_available: int) -> str:
        """Generate explanation for tool selection."""
        if not selected_tools:
            return "🔧 No tools needed for this task"
        
        tool_names = ", ".join(selected_tools)
        
        if self.level == ExplanationLevel.CONCISE:
            return f"🔧 Selected {len(selected_tools)} relevant tools: {tool_names}"
        elif self.level == ExplanationLevel.DETAILED:
            return f"🔧 Analyzed {total_available} available tools and selected {len(selected_tools)} most relevant: {tool_names}"
        else:
            return f"🔧 Tool selection: {len(selected_tools)}/{total_available} tools selected via LLM filtering: {tool_names}"
    
    def explain_tool_usage(self, tool_name: str, tool_input: Dict[str, Any], result_summary: str) -> str:
        """Generate explanation for individual tool usage."""
        action_desc = self._tool_explanations.get(tool_name, f"used {tool_name}")
        
        if self.level == ExplanationLevel.CONCISE:
            return f"⚡ I {action_desc} and {result_summary}"
        elif self.level == ExplanationLevel.DETAILED:
            key_params = self._extract_key_parameters(tool_input)
            param_desc = f" with {key_params}" if key_params else ""
            return f"⚡ I {action_desc}{param_desc} and {result_summary}"
        else:
            return f"⚡ Executed {tool_name}({tool_input}) → {result_summary}"
    
    def explain_reasoning_decision(self, decision_type: str, reasoning: str, confidence: float = None) -> str:
        """Generate explanation for reasoning decisions."""
        confidence_desc = ""
        if confidence is not None and self.level != ExplanationLevel.CONCISE:
            confidence_desc = f" (confidence: {confidence:.1%})"
        
        if decision_type == "direct_response":
            if self.level == ExplanationLevel.CONCISE:
                return f"💡 I can answer this directly"
            else:
                return f"💡 Direct response possible - no tools needed{confidence_desc}"
        
        elif decision_type == "tool_needed":
            if self.level == ExplanationLevel.CONCISE:
                return f"💭 I need to gather more information"
            else:
                return f"💭 Additional information required via tool execution{confidence_desc}"
        
        elif decision_type == "task_complete":
            if self.level == ExplanationLevel.CONCISE:
                return f"✅ Task completed successfully"
            else:
                return f"✅ Task completed - all requirements satisfied{confidence_desc}"
        
        return f"🤔 {reasoning}"
    
    def explain_stopping_criteria(self, stopping_reason: str, metrics: Dict[str, Any]) -> str:
        """Generate explanation for why reasoning stopped."""
        reason_explanations = {
            "confidence_threshold": "reached high confidence in the answer",
            "time_limit": "reached time limit to ensure responsiveness",
            "max_iterations": "completed thorough analysis within iteration limit",
            "diminishing_returns": "additional reasoning wouldn't improve the answer",
            "resource_limit": "used optimal amount of resources",
            "error_threshold": "encountered issues and stopped to prevent errors",
            "task_complete": "successfully completed the task"
        }
        
        explanation = reason_explanations.get(stopping_reason, f"stopped due to {stopping_reason}")
        
        if self.level == ExplanationLevel.CONCISE:
            return f"🏁 Finished reasoning - {explanation}"
        elif self.level == ExplanationLevel.DETAILED:
            iterations = metrics.get('total_iterations', 0)
            time_taken = metrics.get('total_time', 0)
            return f"🏁 Reasoning complete after {iterations} iterations ({time_taken:.1f}s) - {explanation}"
        else:
            return f"🏁 Stopping criteria met: {stopping_reason} - {metrics}"
    
    def explain_memory_action(self, action: str, details: str) -> str:
        """Generate explanation for memory-related actions."""
        if action == "recall":
            if self.level == ExplanationLevel.CONCISE:
                return f"🧠 Recalled relevant information"
            else:
                return f"🧠 Retrieved memories: {details}"
        
        elif action == "memorize":
            if self.level == ExplanationLevel.CONCISE:
                return f"🧠 Saved important information"
            else:
                return f"🧠 Stored for future reference: {details}"
        
        return f"🧠 {action}: {details}"
    
    def explain_error_recovery(self, error_type: str, recovery_action: str) -> str:
        """Generate explanation for error handling and recovery."""
        if self.level == ExplanationLevel.CONCISE:
            return f"⚠️ Encountered issue, trying alternative approach"
        elif self.level == ExplanationLevel.DETAILED:
            return f"⚠️ Handled {error_type} error by {recovery_action}"
        else:
            return f"⚠️ Error recovery: {error_type} → {recovery_action}"
    
    def _describe_complexity(self, max_iterations: int) -> str:
        """Describe query complexity based on iteration limit."""
        if max_iterations <= 2:
            return "simple"
        elif max_iterations <= 4:
            return "moderate"
        else:
            return "complex"
    
    def _extract_key_parameters(self, tool_input: Dict[str, Any]) -> str:
        """Extract key parameters from tool input for explanation."""
        if not tool_input:
            return ""
        
        # Common important parameters
        key_params = []
        for key in ["query", "search_term", "file_path", "url", "question"]:
            if key in tool_input:
                value = str(tool_input[key])
                if len(value) > 30:
                    value = value[:27] + "..."
                key_params.append(f"{key}='{value}'")
        
        return ", ".join(key_params) if key_params else ""


def create_actionable_insights(trace_entries: List[Dict[str, Any]], context: ExplanationContext) -> List[str]:
    """Generate actionable insights from trace entries."""
    insights = []
    
    # Performance insights
    if context.execution_time > 10:
        insights.append("💡 Consider breaking complex requests into smaller parts for faster responses")
    
    # Tool usage insights
    tool_usage = {}
    for entry in trace_entries:
        if "tool" in entry.get("message", "").lower():
            node = entry.get("node", "unknown")
            tool_usage[node] = tool_usage.get(node, 0) + 1
    
    if len(tool_usage) > 5:
        insights.append("💡 Many tools were used - consider more specific requests for efficiency")
    
    # Success/failure insights
    if not context.success:
        insights.append("💡 Task partially completed - try rephrasing or providing more context")
    
    # Stopping reason insights
    if context.stopping_reason == "time_limit":
        insights.append("💡 Time limit reached - complex queries may need more time")
    elif context.stopping_reason == "diminishing_returns":
        insights.append("💡 Optimal solution found - additional processing wouldn't improve results")
    
    return insights