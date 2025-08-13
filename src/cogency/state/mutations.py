"""State mutation functions - conversation message persistence.

Canonical state mutations for message flow. Other state updates use direct
attribute access (state.workspace.*, state.execution.*) following canonical patterns.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from . import State


def add_message(state: "State", role: str, content: str) -> None:
    """Add message to conversation history with automatic persistence."""
    from datetime import datetime

    message = {
        "role": role,
        "content": content,
    }

    # Add to persistent conversation
    state.conversation.messages.append(message)
    state.conversation.last_updated = datetime.now()

    # Update execution context with latest message for LLM context
    state.execution.messages = state.conversation.messages.copy()

    # Update state metadata
    state.last_updated = datetime.now()


def update_from_reasoning(state: "State", reasoning_data: dict[str, Any]) -> None:
    """Update state from LLM reasoning response.

    Canonical entry point for Agent → State integration.
    Uses direct attribute access for most updates, add_message for conversation.
    """
    # Handle conversation messages (the main gap)
    if reasoning_data.get("response"):
        add_message(state, "assistant", reasoning_data["response"])
        # Also set execution response for immediate access
        state.execution.response = reasoning_data["response"]

    # Handle tool calls via direct execution state access (canonical pattern)
    if reasoning_data.get("actions"):
        state.execution.pending_calls = reasoning_data["actions"]

    # Handle workspace updates via direct access (canonical pattern)
    if reasoning_data.get("thinking"):
        state.workspace.thoughts.append(
            {
                "iteration": state.execution.iteration,
                "reasoning": reasoning_data["thinking"],
                "timestamp": state.last_updated,
            }
        )


def set_tool_calls(state: "State", calls: list[dict[str, Any]]) -> None:
    """Set pending tool calls in execution state."""
    state.execution.pending_calls = calls


def finish_tools(state: "State", results: list[dict[str, Any]]) -> None:
    """Move pending calls to completed and store results."""
    from datetime import datetime

    # Move pending calls to completed with results
    state.execution.completed_calls.extend(results)
    state.execution.pending_calls = []

    # Update metadata
    state.last_updated = datetime.now()


__all__ = ["add_message", "update_from_reasoning", "set_tool_calls", "finish_tools"]
