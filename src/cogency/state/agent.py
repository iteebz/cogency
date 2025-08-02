"""AgentState - Complete agent state composition."""

from typing import Any, Dict, Optional

from .execution import ExecutionState
from .memory import UserProfile
from .reasoning import ReasoningContext


class AgentState:
    """Complete agent state - execution + reasoning + situated memory."""

    def __init__(
        self, query: str, user_id: str = "default", user_profile: Optional[UserProfile] = None
    ):
        self.execution = ExecutionState(query=query, user_id=user_id)
        self.reasoning = ReasoningContext(goal=query)
        self.user_profile = user_profile  # Situated memory

    def get_situated_context(self) -> str:
        """Get user context for prompt injection."""
        if not self.user_profile:
            return ""

        context = self.user_profile.compress_for_injection()
        return f"USER CONTEXT:\n{context}\n\n" if context else ""

    def update_from_reasoning(self, reasoning_data: Dict[str, Any]) -> None:
        """Update state from LLM reasoning response."""
        # Record thinking
        thinking = reasoning_data.get("thinking", "")
        tool_calls = reasoning_data.get("tool_calls", [])

        if thinking:
            self.reasoning.record_thinking(thinking, tool_calls)

        # Set tool calls for execution
        if tool_calls:
            self.execution.set_tool_calls(tool_calls)

        # Update reasoning context
        context_updates = reasoning_data.get("context_updates", {})
        if context_updates:
            if "goal" in context_updates:
                self.reasoning.goal = context_updates["goal"]
            if "strategy" in context_updates:
                self.reasoning.strategy = context_updates["strategy"]
            if "insights" in context_updates and isinstance(context_updates["insights"], list):
                for insight in context_updates["insights"]:
                    self.reasoning.add_insight(insight)

        # Handle direct response
        if "response" in reasoning_data and reasoning_data["response"]:
            self.execution.response = reasoning_data["response"]

        # Handle mode switching
        if "switch_mode" in reasoning_data and reasoning_data["switch_mode"]:
            new_mode = reasoning_data["switch_mode"]
            if new_mode in ["fast", "deep", "adapt"]:
                self.execution.mode = new_mode
