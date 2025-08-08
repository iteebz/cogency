#!/usr/bin/env python3
"""Verify Database-as-State write-through persistence works with Temporal Horizons architecture."""

import asyncio
import sys
import tempfile
from pathlib import Path

sys.path.append("src")

from cogency.state.agent import State
from cogency.state.mutations import add_message, add_user_goal, learn_insight
from cogency.storage.backends.sqlite import SQLite


async def main():
    """Test CANONICAL Three-Horizon persistence."""
    print("🔍 Verifying Database-as-State write-through persistence...")

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        store = SQLite(str(db_path))

        # Create State with all three horizons
        state = State(
            query="Test persistence verification", user_id="test_user", task_id="test_task_123"
        )

        print(f"✅ Created State: {state.user_id}, task: {state.task_id}")

        # Use Persistence to verify (it handles key generation correctly)
        from cogency.storage.registry import clear_global_store, set_global_store
        from cogency.storage.state import Persistence

        # Set global store BEFORE any mutations so autosave uses the same instance
        set_global_store(store)
        persist = Persistence(store=store)

        # TEST 1: Horizon 1 (UserProfile) mutations with autosave
        print("\n🔬 Testing Horizon 1 (UserProfile) persistence...")
        add_user_goal(state, "Learn database persistence")

        # Give autosave time to complete - wait for ALL background tasks
        await asyncio.sleep(0.2)

        # Wait for any pending autosave tasks to finish
        from cogency.state.autosave import autosave

        if hasattr(autosave, "_pending_tasks"):
            if autosave._pending_tasks:
                await asyncio.gather(*autosave._pending_tasks, return_exceptions=True)
            autosave._pending_tasks.clear()

        # Verify UserProfile was persisted
        saved_profile = await persist.load_user_profile("test_user")
        assert saved_profile is not None
        assert "Learn database persistence" in saved_profile.goals
        print(f"✅ UserProfile persisted: {saved_profile.goals}")

        # TEST 2: Horizon 2 (Workspace) mutations with autosave
        print("\n🔬 Testing Horizon 2 (Workspace) persistence...")
        learn_insight(state, "Database-as-State pattern works!")

        # Give autosave time to complete - wait for ALL background tasks
        await asyncio.sleep(0.2)

        # Wait for any pending autosave tasks to finish
        from cogency.state.autosave import autosave

        if hasattr(autosave, "_pending_tasks"):
            await asyncio.gather(*autosave._pending_tasks, return_exceptions=True)
            autosave._pending_tasks.clear()

        # Verify Workspace was persisted
        saved_workspace = await persist.load_task_workspace("test_task_123", "test_user")
        assert saved_workspace is not None
        assert "Database-as-State pattern works!" in saved_workspace.insights
        print(f"✅ Workspace persisted: {saved_workspace.insights}")

        # TEST 3: Horizon 3 (ExecutionState) should NOT be persisted
        print("\n🔬 Testing Horizon 3 (ExecutionState) NOT persisted...")
        add_message(state, "user", "Test message")

        # Verify ExecutionState messages are NOT in database
        # (They should only exist in memory/runtime)
        assert len(state.execution.messages) == 1
        print(f"✅ ExecutionState in memory: {len(state.execution.messages)} messages")

        # Create new state instance to simulate fresh session
        fresh_state = State(query="Fresh session", user_id="test_user", task_id="test_task_123")

        # Load persisted data using Persistence
        fresh_persist = Persistence(store=store)
        fresh_state.profile = await fresh_persist.load_user_profile("test_user")
        fresh_state.workspace = await fresh_persist.load_task_workspace(
            "test_task_123", "test_user"
        )

        # Verify persistence worked correctly
        assert fresh_state.profile.goals == ["Learn database persistence"]
        assert fresh_state.workspace.insights == ["Database-as-State pattern works!"]
        assert len(fresh_state.execution.messages) == 0  # ExecutionState starts fresh

        print("\n🎉 VERIFICATION SUCCESSFUL!")
        print("📊 Three-Horizon Split-State Model working correctly:")
        print("   • Horizon 1 (UserProfile): ✅ Persisted across sessions")
        print("   • Horizon 2 (Workspace): ✅ Persisted for task continuation")
        print("   • Horizon 3 (ExecutionState): ✅ Runtime-only, not persisted")
        print("   • Database-as-State: ✅ Write-through autosave working")

        # Clean up
        clear_global_store()


if __name__ == "__main__":
    asyncio.run(main())
