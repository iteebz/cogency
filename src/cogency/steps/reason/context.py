"""Context building for reasoning."""

from typing import Any, Dict, List

from cogency.state import AgentState
from cogency.tools import Tool
from cogency.tools.registry import build_registry


class Context:
    """Builds unified context for reasoning prompts."""

    async def build(
        self, state: AgentState, selected_tools: List[Tool], memory, mode: str, iteration: int
    ) -> Dict[str, Any]:
        """Build complete context data for reasoning."""
        # Build tool registry
        tool_registry = build_registry(selected_tools)

        # Build reasoning context from state
        max_history = 3
        reasoning_context = state.reasoning_context(mode, max_history=max_history)

        # Get memory context if available
        memory_context = ""
        if memory:
            impression_data = await memory.recall()
            if impression_data:
                memory_context = f"{impression_data}\n"

        return {
            "tool_registry": tool_registry,
            "reasoning_context": reasoning_context,
            "memory_context": memory_context,
            "workspace_context": state.workspace_context(),
        }
