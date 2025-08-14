"""Working state operations - cognitive state management.

All working state lifecycle management and reasoning integration
centralized in the working domain.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import WorkingState

if TYPE_CHECKING:
    from cogency.storage.sqlite import SQLite


def create_working_state(objective: str) -> WorkingState:
    """Create fresh working state for new task."""
    return WorkingState(objective=objective)


async def save_working_state(task_id: str, user_id: str, working_state: WorkingState, store: "SQLite") -> bool:
    """Save working state to storage."""
    # Convert to legacy Workspace format for storage compatibility
    # TODO: Update storage to use WorkingState directly
    from cogency.state import Workspace
    
    workspace = Workspace(
        objective=working_state.objective,
        assessment=working_state.understanding,  # Map understanding -> assessment
        approach=working_state.approach,
        observations=[],  # Empty - not used in 4-field design
        insights=[working_state.discoveries] if working_state.discoveries else [],  # Map discoveries -> insights
        facts={},  # Empty - not used in 4-field design
        thoughts=[],  # Empty - not used in 4-field design
    )
    
    return await store.save_workspace(task_id, user_id, workspace)


async def load_working_state(task_id: str, user_id: str, store: "SQLite") -> WorkingState | None:
    """Load working state from storage."""
    workspace = await store.load_workspace(task_id, user_id)
    if not workspace:
        return None
    
    # Convert from legacy Workspace format
    understanding = workspace.assessment if hasattr(workspace, 'assessment') else ""
    discoveries = workspace.insights[0] if (hasattr(workspace, 'insights') and workspace.insights) else ""
    
    return WorkingState(
        objective=workspace.objective,
        understanding=understanding,
        approach=workspace.approach,
        discoveries=discoveries,
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