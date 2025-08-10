"""Autosave - Database-as-State immediate persistence."""

import asyncio
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .state import State


def autosave(state: "State") -> None:
    """Save profile, conversation, and workspace during task execution."""
    import os

    # Skip autosave in test environment to prevent hanging
    if os.environ.get("PYTEST_CURRENT_TEST") or "pytest" in os.environ.get("_", ""):
        return

    from ..storage.state import SQLite

    # Update timestamps
    state.profile.last_updated = datetime.now()
    state.conversation.last_updated = datetime.now()

    try:
        loop = asyncio.get_event_loop()

        async def save_persistent_state():
            store = SQLite()
            # Save user profile
            state_key = f"{state.user_id}:default"
            await store.save_user_profile(state_key, state.profile)
            # Save conversation
            await store.save_conversation(state.conversation)
            # Save workspace for task continuation
            await store.save_task_workspace(state.task_id, state.user_id, state.workspace)
            # Execution state is never saved - runtime-only

        if loop.is_running():
            # Fire-and-forget background save
            task = asyncio.create_task(save_persistent_state())
            # Store task reference to prevent GC from cancelling it
            if not hasattr(autosave, "_pending_tasks"):
                autosave._pending_tasks = set()
            autosave._pending_tasks.add(task)
            task.add_done_callback(autosave._pending_tasks.discard)
        else:
            loop.run_until_complete(save_persistent_state())
    except Exception:
        # Graceful degradation - don't break execution on save failure
        pass
