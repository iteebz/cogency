"""Cogency State - Zero ceremony, maximum beauty."""

import asyncio
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from cogency.constants import DEFAULT_MAX_ITERATIONS, MAX_FAILURES_HISTORY, MAX_ITERATIONS_HISTORY
from cogency.context import Context


@dataclass 
class State:
    """Clean dataclass state for LangGraph compatibility."""
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

    def track_failure(self, tool_calls: List[Any], quality: str) -> None:
        """Track failed tool attempts."""
        failure_entry = {
            "tool_calls": tool_calls,
            "quality": quality,
            "iteration": self.iteration,
        }
        self.attempts.append(failure_entry)

        # Enforce failure history limit
        if len(self.attempts) > MAX_FAILURES_HISTORY:
            self.attempts = self.attempts[-MAX_FAILURES_HISTORY:]


# Export clean State class

# Function to compress actions into attempts for LLM prompting
def compress_actions(actions: List[Dict[str, Any]]) -> List[str]:
    """Phase 1: Basic compression of actions to readable format."""
    compressed = []
    for action in actions:
        for call in action.get("tool_calls", []):
            tool = call.get("tool", "unknown")
            outcome = call.get("outcome", "unknown") 
            params = call.get("params", {})
            # Simple readable format for Phase 1
            params_summary = str(params)[:50] + "..." if len(str(params)) > 50 else str(params)
            compressed.append(f"{tool}({params_summary}) → {outcome}")
    return compressed
