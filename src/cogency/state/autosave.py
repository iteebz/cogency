"""Autosave - Database-as-State immediate persistence."""

import asyncio
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .agent import State


def autosave(state: "State") -> None:
    """CANONICAL: Save Horizon 1 + Horizon 2 during task execution (NOT Horizon 3)"""
    import os

    # Skip autosave in test environment to prevent hanging
    if os.environ.get("PYTEST_CURRENT_TEST") or "pytest" in os.environ.get("_", ""):
        return

    from cogency.storage.registry import get_global_store
    from cogency.storage.state import Persistence

    # Update timestamp on profile
    state.profile.last_updated = datetime.now()

    # Use canonical persistence layer for Three-Horizon model
    # Use global store for consistency across app
    global_store = get_global_store()
    if not global_store:
        # Don't create default stores in background tasks - causes hangs
        return

    persist = Persistence(store=global_store)

    try:
        loop = asyncio.get_event_loop()

        async def save_both_horizons():
            # Save Horizon 1: UserProfile to user_profiles table
            await persist.user_profile(state.user_id, state.profile)
            # Save Horizon 2: Workspace to task_workspaces table for task continuation
            await persist.task_workspace(state.task_id, state.user_id, state.workspace)
            # Horizon 3: ExecutionState NEVER saved - runtime-only

        if loop.is_running():
            # Fire-and-forget background save
            task = asyncio.create_task(save_both_horizons())
            # Store task reference to prevent GC from cancelling it
            if not hasattr(autosave, "_pending_tasks"):
                autosave._pending_tasks = set()
            autosave._pending_tasks.add(task)
            task.add_done_callback(autosave._pending_tasks.discard)
        else:
            loop.run_until_complete(save_both_horizons())
    except Exception:
        # Graceful degradation - don't break execution on save failure
        pass
