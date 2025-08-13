"""Integration tests for SQLite persistence store."""

import tempfile
from pathlib import Path

import pytest

from cogency.memory import Profile
from cogency.state import State
from cogency.storage.sqlite import SQLite


@pytest.mark.asyncio
async def test_basic_operations():
    """Test basic save/load/delete operations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        store = SQLite(str(db_path))

        # Create test state and profile
        from cogency.memory.memory import Profile
        from cogency.state.mutations import add_message

        state = State(query="test query", user_id="test_user")
        add_message(state, "user", "Hello")
        state.execution.iteration = 3

        # Create profile separately (profiles come from memory system, not state)
        profile = Profile(user_id="test_user")

        # Save using canonical methods
        await store.save_profile("test_user:default", profile)

        # Load using canonical methods
        loaded_profile = await store.load_profile("test_user:default")

        assert loaded_profile is not None
        assert loaded_profile.user_id == "test_user"

        # Delete using canonical methods
        deleted_profile = await store.delete_profile("test_user:default")
        assert deleted_profile is True

        # Verify deletion
        loaded_after_delete_profile = await store.load_profile("test_user:default")
        assert loaded_after_delete_profile is None


@pytest.mark.asyncio
async def test_with_user_profile():
    """Test state with user profile."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        store = SQLite(str(db_path))

        # Create profile (profiles are separate from state now)
        from cogency.state.mutations import add_message

        profile = Profile(user_id="test_user")
        profile.preferences = {"language": "Python", "style": "concise"}

        # Create state (no profile attached)
        state = State(query="test query", user_id="test_user")
        add_message(state, "assistant", "Response")

        # Save and load using canonical methods
        await store.save_profile("test_user:default", profile)

        loaded_profile = await store.load_profile("test_user:default")

        assert loaded_profile is not None
        assert loaded_profile.user_id == "test_user"
        assert loaded_profile.preferences["language"] == "Python"


@pytest.mark.asyncio
async def test_profile_operations():
    """Test separate profile save/load operations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        store = SQLite(str(db_path))

        # Create profile using canonical structure
        from cogency.memory import Profile

        profile = Profile(user_id="profile_user")
        profile.preferences = {"theme": "dark"}

        # Save profile using canonical method
        success = await store.save_profile("profile_user:default", profile)
        assert success is True

        # Load profile using canonical method
        loaded_profile = await store.load_profile("profile_user:default")
        assert loaded_profile is not None
        assert loaded_profile.user_id == "profile_user"
        assert loaded_profile.preferences["theme"] == "dark"

        # Delete profile using canonical method
        deleted = await store.delete_profile("profile_user:default")
        assert deleted is True

        # Verify deletion
        loaded_after_delete = await store.load_profile("profile_user:default")
        assert loaded_after_delete is None
