"""Cogency State - Zero ceremony, maximum beauty."""

import asyncio
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from cogency.constants import DEFAULT_MAX_ITERATIONS, MAX_FAILURES_HISTORY, MAX_ITERATIONS_HISTORY
from cogency.types.outcomes import ToolOutcome


@dataclass 
class State:
    """Clean dataclass state for agent execution."""
    # Core execution context
    query: str
    user_id: str = "default"
    messages: List[Dict[str, str]] = field(default_factory=list)
    # Flow control  
    iteration: int = 0
    max_iterations: int = DEFAULT_MAX_ITERATIONS
    react_mode: str = "fast"
    stop_reason: Optional[str] = None
    # Tool execution
    selected_tools: List[Any] = field(default_factory=list)
    tool_calls: List[Any] = field(default_factory=list)
    result: Any = None
    # Two-layer state architecture
    actions: List[Dict[str, Any]] = field(default_factory=list)
    attempts: List[Any] = field(default_factory=list)
    current_approach: str = "initial"
    # Phase 2B: Semantic context summarization
    situation_summary: Dict[str, str] = field(default_factory=lambda: {
        "goal": "",
        "progress": "", 
        "current_approach": "",
        "key_findings": "",
        "next_focus": ""
    })
    # Output
    response: Optional[str] = None
    respond_directly: bool = False
    verbose: bool = True
    trace: bool = False
    callback: Any = None
    notifications: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_message(self, role: str, content: str) -> None:
        """Add message to conversation history."""
        self.messages.append({"role": role, "content": content})
    
    def get_conversation(self) -> List[Dict[str, str]]:
        """Get clean conversation for LLM."""
        return [{"role": msg["role"], "content": msg["content"]} for msg in self.messages]
    
    
    def add_action(
        self,
        mode: str,
        thinking: str,
        planning: str,
        reflection: str,
        approach: str,
        tool_calls: List[Any],
    ) -> None:
        """Add action to reasoning history with new schema."""
        from datetime import datetime
        
        self.current_approach = approach
        
        action_entry = {
            "iteration": self.iteration,
            "timestamp": datetime.now().isoformat(),
            "mode": mode,
            "thinking": thinking,
            "planning": planning,
            "reflection": reflection,
            "approach": approach,
            "tool_calls": tool_calls,
            # NO compression fields - handled by situation_summary
        }
        self.actions.append(action_entry)

        # Enforce history limit
        if len(self.actions) > MAX_ITERATIONS_HISTORY:
            self.actions = self.actions[-MAX_ITERATIONS_HISTORY:]

    def add_tool_result(
        self,
        name: str,
        args: dict,
        result: str,
        outcome: ToolOutcome,
        iteration: Optional[int] = None
    ) -> None:
        """Add tool execution result to current action (schema-compliant)."""
        if not self.actions:
            raise ValueError("Cannot add tool result without an active action")
        
        current_action = self.actions[-1]
        tool_call = {
            "name": name,
            "args": args,
            "result": result[:1000],  # Truncate per schema
            "outcome": outcome.value,
            # NO compression fields - handled by situation_summary
        }
        
        # Initialize tool_calls if needed
        if "tool_calls" not in current_action:
            current_action["tool_calls"] = []
        
        current_action["tool_calls"].append(tool_call)

    def get_latest_results(self) -> List[Dict[str, Any]]:
        """Get tool results from most recent action."""
        if not self.actions:
            return []
        
        latest_action = self.actions[-1]
        return latest_action.get("tool_calls", [])

    def get_compressed_attempts(self, max_history: int = 3) -> List[str]:
        """Get compressed attempts using semantic context summarization."""
        if len(self.actions) <= 1:
            return []
        
        # Phase 2B: Return situation_summary instead of compressed strings
        if any(v.strip() for v in self.situation_summary.values()):
            # Convert summary to readable format for reasoning context
            summary_parts = []
            for key, value in self.situation_summary.items():
                if value.strip():
                    summary_parts.append(f"{key}: {value}")
            return ["; ".join(summary_parts)] if summary_parts else []
        
        # Fallback to basic compression if summary empty
        past_actions = self.actions[:-1][-max_history:]
        return compress_actions(past_actions)

    def format_actions_for_fast_mode(self, max_history: int = 3) -> str:
        """Format actions as simple compressed string for fast mode."""
        compressed = self.get_compressed_attempts(max_history)
        return "; ".join(compressed) if compressed else "No previous attempts"

    def format_actions_for_deep_mode(self, max_history: int = 3) -> str:
        """Format structured actions with full context for deep mode reflection."""
        if not self.actions:
            return "No previous actions"
        
        formatted = []
        for action in self.actions[-max_history:]:
            iter_num = action.get("iteration", "?")
            mode = action.get("mode", "unknown")
            thinking = action.get("thinking", "")
            planning = action.get("planning", "")
            reflection = action.get("reflection", "")
            
            # Format action header
            action_header = f"[Iteration {iter_num}] {mode.upper()} mode:"
            parts = [action_header]
            
            if thinking:
                parts.append(f"  Thinking: {thinking[:200]}{'...' if len(thinking) > 200 else ''}")
            if planning:
                parts.append(f"  Planning: {planning[:200]}{'...' if len(planning) > 200 else ''}")
            if reflection:
                parts.append(f"  Reflection: {reflection[:200]}{'...' if len(reflection) > 200 else ''}")
            
            # Format tool outcomes
            tool_calls = action.get("tool_calls", [])
            if tool_calls:
                parts.append("  Tool Outcomes:")
                for call in tool_calls:
                    name = call.get("name", "unknown")
                    outcome = call.get("outcome", "unknown")
                    result_snippet = call.get("result", "")[:100] + ("..." if len(call.get("result", "")) > 100 else "")
                    parts.append(f"    {name}() → {outcome}: {result_snippet}")
            
            formatted.append("\n".join(parts))
        
        return "\n\n".join(formatted)

    def format_latest_results_detailed(self) -> str:
        """Format latest tool results with full detail for deep mode analysis."""
        latest_results = self.get_latest_results()
        if not latest_results:
            return "No tool results from current iteration"
        
        formatted = []
        for call in latest_results:
            name = call.get("name", "unknown")
            args = call.get("args", {})
            outcome = call.get("outcome", "unknown")
            result = call.get("result", "")
            
            # Show full result for current iteration analysis
            formatted.append(f"{name}({args}) → {outcome}")
            if result:
                formatted.append(f"  Result: {result}")
        
        return "\n".join(formatted)

    def build_reasoning_context(self, mode: str, max_history: int = 3) -> str:
        """Phase 3: Clean context assembly for reasoning with semantic compression."""
        if mode == "deep":
            # Deep mode: situation_summary + latest action details
            summary_context = self.format_actions_for_fast_mode(max_history)
            latest_context = self.format_latest_results_detailed()
            
            if summary_context == "No previous attempts":
                return latest_context if latest_context else "No context available"
            elif latest_context == "No tool results from current iteration":
                return summary_context
            else:
                return f"{summary_context}\n\nLATEST DETAILS:\n{latest_context}"
        else:
            # Fast mode: just situation_summary
            return self.format_actions_for_fast_mode(max_history)



# Export clean State class

# Function to compress actions into attempts for LLM prompting
def compress_actions(actions: List[Dict[str, Any]]) -> List[str]:
    """Phase 1: Basic compression of actions to readable format (schema-compliant)."""
    compressed = []
    for action in actions:
        for call in action.get("tool_calls", []):
            name = call.get("name", "unknown")
            args = call.get("args", {})
            outcome = call.get("outcome", "unknown")
            result = call.get("result", "")
            
            # Format: tool(args) → outcome: result_snippet
            args_summary = str(args)[:20] + "..." if len(str(args)) > 20 else str(args)
            result_snippet = result[:50] + "..." if len(result) > 50 else result
            
            if result_snippet:
                compressed.append(f"{name}({args_summary}) → {outcome}: {result_snippet}")
            else:
                compressed.append(f"{name}({args_summary}) → {outcome}")
    
    return compressed
