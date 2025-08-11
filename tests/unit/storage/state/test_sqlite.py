"""Integration tests for SQLite persistence store."""

import tempfile
from pathlib import Path

import pytest

from cogency.state import Profile, State
from cogency.storage.state import SQLite


@pytest.mark.asyncio
async def test_basic_operations():
    """Test basic save/load/delete operations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        store = SQLite(str(db_path))

        # Create test state
        from cogency.state.mutations import add_message, learn_insight

        state = State(query="test query", user_id="test_user")
        add_message(state, "user", "Hello")
        state.execution.iteration = 3
        learn_insight(state, "Test insight")

        # Save using canonical methods
        await store.save_profile("test_user:default", state.profile)
        await store.save_workspace(state.task_id, "test_user", state.workspace)

        # Load using canonical methods
        loaded_profile = await store.load_profile("test_user:default")
        loaded_workspace = await store.load_workspace(state.task_id, "test_user")

        assert loaded_profile is not None
        assert loaded_workspace is not None
        assert loaded_profile.user_id == "test_user"
        assert loaded_workspace.objective == "test query"
        assert "Test insight" in loaded_workspace.insights

        # Delete using canonical methods
        deleted_workspace = await store.clear_workspace(state.task_id)
        deleted_profile = await store.delete_profile("test_user:default")
        assert deleted_workspace is True
        assert deleted_profile is True

        # Verify deletion
        loaded_after_delete_profile = await store.load_profile("test_user:default")
        loaded_after_delete_workspace = await store.load_workspace(state.task_id, "test_user")
        assert loaded_after_delete_profile is None
        assert loaded_after_delete_workspace is None


@pytest.mark.asyncio
async def test_with_user_profile():
    """Test state with user profile."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        store = SQLite(str(db_path))

        # Create profile
        profile = Profile(user_id="test_user")
        profile.preferences = {"language": "Python", "style": "concise"}
        profile.communication_style = "technical"

        # Create state with profile
        from cogency.state.mutations import add_message

        state = State(query="test query", user_id="test_user")
        state.profile = profile
        add_message(state, "assistant", "Response")

        # Save and load using canonical methods
        await store.save_profile("test_user:default", state.profile)
        await store.save_workspace(state.task_id, "test_user", state.workspace)

        loaded_profile = await store.load_profile("test_user:default")
        loaded_workspace = await store.load_workspace(state.task_id, "test_user")

        assert loaded_profile is not None
        assert loaded_workspace is not None
        assert loaded_profile.user_id == "test_user"
        assert loaded_profile.preferences["language"] == "Python"
        assert loaded_profile.communication_style == "technical"


@pytest.mark.asyncio
async def test_profile_operations():
    """Test separate profile save/load operations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        store = SQLite(str(db_path))

        # Create profile using canonical structure
        from cogency.state import Profile

        profile = Profile(user_id="profile_user")
        profile.preferences = {"theme": "dark"}
        profile.communication_style = "casual"

        # Save profile using canonical method
        success = await store.save_profile("profile_user:default", profile)
        assert success is True

        # Load profile using canonical method
        loaded_profile = await store.load_profile("profile_user:default")
        assert loaded_profile is not None
        assert loaded_profile.user_id == "profile_user"
        assert loaded_profile.preferences["theme"] == "dark"
        assert loaded_profile.communication_style == "casual"

        # Delete profile using canonical method
        deleted = await store.delete_profile("profile_user:default")
        assert deleted is True

        # Verify deletion
        loaded_after_delete = await store.load_profile("profile_user:default")
        assert loaded_after_delete is None


@pytest.mark.asyncio
async def test_list_states():
    """Test listing states for a user."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        store = SQLite(str(db_path))

        # Create multiple workspaces for same user
        state1 = State(query="query1", user_id="multi_user")
        state2 = State(query="query2", user_id="multi_user")

        await store.save_workspace(state1.task_id, "multi_user", state1.workspace)
        await store.save_workspace(state2.task_id, "multi_user", state2.workspace)

        # List workspaces using canonical method
        workspace_ids = await store.list_workspaces("multi_user")
        assert len(workspace_ids) == 2
        assert state1.task_id in workspace_ids
        assert state2.task_id in workspace_ids


@pytest.mark.asyncio
async def test_query_states():
    """Test querying states with metadata."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        store = SQLite(str(db_path))

        # Create workspaces for different users
        state1 = State(query="query1", user_id="query_user1")
        state2 = State(query="query2", user_id="query_user2")

        # Add some test data to workspaces
        state1.workspace.insights = ["fast insight"]
        state2.workspace.insights = ["deep insight"]

        await store.save_workspace(state1.task_id, "query_user1", state1.workspace)
        await store.save_workspace(state2.task_id, "query_user2", state2.workspace)

        # Test workspace listing for each user
        user1_workspaces = await store.list_workspaces("query_user1")
        user2_workspaces = await store.list_workspaces("query_user2")

        assert len(user1_workspaces) == 1
        assert len(user2_workspaces) == 1
        assert state1.task_id in user1_workspaces
        assert state2.task_id in user2_workspaces

        # Test loading specific workspaces
        loaded1 = await store.load_workspace(state1.task_id, "query_user1")
        loaded2 = await store.load_workspace(state2.task_id, "query_user2")

        assert "fast insight" in loaded1.insights
        assert "deep insight" in loaded2.insights


@pytest.mark.asyncio
async def test_concurrent_access():
    """Test concurrent read/write operations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "concurrent.db"

        # Create multiple store instances (simulating concurrent access)
        store1 = SQLite(str(db_path))
        store2 = SQLite(str(db_path))

        # Concurrent writes using canonical methods
        state1 = State(query="concurrent1", user_id="concurrent_user1")
        state2 = State(query="concurrent2", user_id="concurrent_user2")

        import asyncio

        # Concurrent workspace saves
        results = await asyncio.gather(
            store1.save_workspace(state1.task_id, "concurrent_user1", state1.workspace),
            store2.save_workspace(state2.task_id, "concurrent_user2", state2.workspace),
        )

        assert all(results)  # Both saves should succeed

        # Concurrent reads
        loaded_workspaces = await asyncio.gather(
            store1.load_workspace(state1.task_id, "concurrent_user1"),
            store2.load_workspace(state2.task_id, "concurrent_user2"),
        )

        assert loaded_workspaces[0] is not None
        assert loaded_workspaces[1] is not None
        assert loaded_workspaces[0].objective == "concurrent1"
        assert loaded_workspaces[1].objective == "concurrent2"


@pytest.mark.asyncio
async def test_schema_evolution():
    """Test that the store handles schema creation properly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "schema.db"

        # First store instance creates schema and saves data
        store1 = SQLite(str(db_path))
        state = State(query="schema test", user_id="schema_user")

        # Save using canonical methods
        profile_success = await store1.save_profile("schema_user:default", state.profile)
        workspace_success = await store1.save_workspace(
            state.task_id, "schema_user", state.workspace
        )
        assert profile_success is True
        assert workspace_success is True

        # Second store instance uses existing schema
        store2 = SQLite(str(db_path))
        loaded_profile = await store2.load_profile("schema_user:default")
        loaded_workspace = await store2.load_workspace(state.task_id, "schema_user")

        assert loaded_profile is not None
        assert loaded_workspace is not None
        assert loaded_workspace.objective == "schema test"
