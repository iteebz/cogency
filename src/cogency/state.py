"""Cogency State - Zero ceremony, maximum beauty."""

import asyncio
from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from cogency.constants import DEFAULT_MAX_ITERATIONS, MAX_FAILURES_HISTORY, MAX_ITERATIONS_HISTORY
from cogency.context import Context


class ToolOutcome(Enum):
    """Tool execution outcomes matching schema."""
    SUCCESS = "success"
    FAILURE = "failure" 
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass 
class State:
    """Clean dataclass state for agent execution."""
    # Core immutable
    context: Context
    query: str
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
    # Output
    response: Optional[str] = None
    respond_directly: bool = False
    verbose: bool = True
    trace: bool = False
    callback: Any = None
    
    async def notify(self, event_type: str, data: Any) -> None:
        """Notify user of progress."""
        if self.callback and self.verbose and callable(self.callback):
            if asyncio.iscoroutinefunction(self.callback):
                await self.callback(str(data))
            else:
                self.callback(str(data))
    
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
            # Phase 2 compression fields (empty for now)
            "synthesis": "",
            "progress": "",
            "hypothesis": {"belief": "", "test": ""},
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
            # Phase 2 fields - empty for now
            "insights": "",
            "learning": "",
            "relevance": "",
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
        """Get compressed attempts using schema-compliant compress_actions."""
        if len(self.actions) <= 1:
            return []
        
        # Compress all but the latest action
        past_actions = self.actions[:-1][-max_history:]
        return compress_actions(past_actions)



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
