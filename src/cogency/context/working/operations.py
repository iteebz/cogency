"""Working state operations - cognitive state management.

All working state lifecycle management and reasoning integration
centralized in the working domain.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .types import WorkingState

if TYPE_CHECKING:
    pass  # No longer need SQLite class


def create_working_state(objective: str) -> WorkingState:
    """Create fresh working state for new task."""
    return WorkingState(objective=objective)


async def save_working_state(
    task_id: str, user_id: str, working_state: WorkingState, db_path: str = None
) -> bool:
    """Save working state to storage using primitive data operations."""
    # Convert WorkingState to primitive data for storage - canonical 4-field design
    workspace_data = {
        "objective": working_state.objective,
        "understanding": working_state.understanding,
        "approach": working_state.approach,
        "discoveries": working_state.discoveries,
    }

    from cogency.storage.sqlite.workspaces import save_workspace_data

    return await save_workspace_data(task_id, user_id, workspace_data, db_path)


async def load_working_state(
    task_id: str, user_id: str, db_path: str = None
) -> WorkingState | None:
    """Load working state from storage using primitive data operations."""
    from cogency.storage.sqlite.workspaces import load_workspace_data

    workspace_data = await load_workspace_data(task_id, user_id, db_path)
    if not workspace_data:
        return None

    # Extract WorkingState from primitive data - canonical 4-field design
    return WorkingState(
        objective=workspace_data.get("objective", ""),
        understanding=workspace_data.get("understanding", ""),
        approach=workspace_data.get("approach", ""),
        discoveries=workspace_data.get("discoveries", ""),
    )


def update_working_state(working_state: WorkingState, reasoning_data: dict) -> None:
    """Update working state from reasoning results.

    Args:
        working_state: Target working state
        reasoning_data: LLM reasoning response with 4-field updates
    """
    if reasoning_data.get("objective"):
        working_state.objective = reasoning_data["objective"]

    if reasoning_data.get("understanding"):
        working_state.understanding = reasoning_data["understanding"]

    if reasoning_data.get("approach"):
        working_state.approach = reasoning_data["approach"]

    if reasoning_data.get("discoveries"):
        working_state.discoveries = reasoning_data["discoveries"]


__all__ = [
    "create_working_state",
    "save_working_state",
    "load_working_state",
    "update_working_state",
]
