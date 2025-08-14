"""Working state subdomain - ephemeral task-scoped cognitive context.

WORKING STATE SCOPE:
Working state is the agent's ephemeral cognitive state during task execution.
It provides structured thinking space for multi-step reasoning and gets cleared
between tasks.

CURRENT IMPLEMENTATION:
Clean 4-field design optimized for natural LLM reasoning flows:
- objective: What we're trying to achieve
- understanding: What we've learned and know
- approach: How we're tackling this systematically
- discoveries: Key insights, patterns, breakthroughs

ARCHITECTURAL PRINCIPLE:
Working state is cognitive scaffolding for reasoning - temporary, task-scoped,
and designed for natural LLM thought processes without artificial constraints.
"""

from __future__ import annotations

# Import types and operations for single-import convenience
from .operations import (
    create_working_state,
    load_working_state,
    save_working_state,
    update_working_state,
)
from .types import WorkingState


async def build_working_context(working_state: WorkingState) -> str | None:
    """Build working context from 4-field working state."""
    if not working_state:
        return None

    parts = []
    if working_state.objective:
        parts.append(f"OBJECTIVE: {working_state.objective}")
    if working_state.understanding:
        parts.append(f"UNDERSTANDING: {working_state.understanding}")
    if working_state.approach:
        parts.append(f"APPROACH: {working_state.approach}")
    if working_state.discoveries:
        parts.append(f"DISCOVERIES: {working_state.discoveries}")

    return "\n".join(parts) if parts else None


__all__ = [
    "WorkingState",
    "build_working_context",
    # Operations
    "create_working_state",
    "save_working_state",
    "load_working_state",
    "update_working_state",
]
