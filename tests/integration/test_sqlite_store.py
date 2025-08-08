"""Integration tests for SQLite persistence store."""

import tempfile
from pathlib import Path

import pytest

from cogency.persist.store.sqlite import SQLiteStore
from cogency.state import AgentState
from cogency.state.user import UserProfile


@pytest.mark.asyncio
async def test_sqlite_store_basic_operations():
    """Test basic save/load/delete operations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        store = SQLiteStore(str(db_path))

        # Create test state
        state = AgentState(query="test query", user_id="test_user")
        state.execution.add_message("user", "Hello")
        state.execution.iteration = 3
        state.reasoning.learn("Test insight")

        # Save state
        success = await store.save("test_user:process1", state)
        assert success is True

        # Load state
        loaded_data = await store.load("test_user:process1")
        assert loaded_data is not None
        assert loaded_data["state"]["execution"]["query"] == "test query"
        assert loaded_data["state"]["execution"]["user_id"] == "test_user"
        assert loaded_data["state"]["execution"]["iteration"] == 3
        assert len(loaded_data["state"]["execution"]["messages"]) == 1
        assert "Test insight" in loaded_data["state"]["reasoning"]["insights"]

        # Delete state
        deleted = await store.delete("test_user:process1")
        assert deleted is True

        # Verify deletion
        loaded_after_delete = await store.load("test_user:process1")
        assert loaded_after_delete is None


@pytest.mark.asyncio
async def test_sqlite_store_with_user_profile():
    """Test state with user profile."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        store = SQLiteStore(str(db_path))

        # Create profile
        profile = UserProfile(user_id="test_user")
        profile.preferences = {"language": "Python", "style": "concise"}
        profile.communication_style = "technical"

        # Create state with profile
        state = AgentState(query="test query", user_id="test_user", user_profile=profile)
        state.execution.add_message("assistant", "Response")

        # Save and load
        await store.save("test_user:session1", state)
        loaded_data = await store.load("test_user:session1")

        assert loaded_data is not None
        user_profile_data = loaded_data["state"]["user_profile"]
        assert user_profile_data is not None
        assert user_profile_data["user_id"] == "test_user"
        assert user_profile_data["preferences"]["language"] == "Python"
        assert user_profile_data["communication_style"] == "technical"


@pytest.mark.asyncio
async def test_sqlite_store_profile_operations():
    """Test separate profile save/load operations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        store = SQLiteStore(str(db_path))

        # Create profile data
        profile_data = {
            "state": {
                "user_id": "profile_user",
                "preferences": {"theme": "dark"},
                "communication_style": "casual",
            }
        }

        # Save profile
        success = await store.save("profile:profile_user", profile_data)
        assert success is True

        # Load profile
        loaded_profile = await store.load("profile:profile_user")
        assert loaded_profile is not None
        assert loaded_profile["state"]["user_id"] == "profile_user"
        assert loaded_profile["state"]["preferences"]["theme"] == "dark"

        # Delete profile
        deleted = await store.delete("profile:profile_user")
        assert deleted is True

        # Verify deletion
        loaded_after_delete = await store.load("profile:profile_user")
        assert loaded_after_delete is None


@pytest.mark.asyncio
async def test_sqlite_store_list_states():
    """Test listing states for a user."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        store = SQLiteStore(str(db_path))

        # Create multiple states for same user
        state1 = AgentState(query="query1", user_id="multi_user")
        state2 = AgentState(query="query2", user_id="multi_user")

        await store.save("multi_user:session1", state1)
        await store.save("multi_user:session2", state2)

        # List states
        state_keys = await store.list_states("multi_user")
        assert len(state_keys) == 2
        assert "multi_user:default" in state_keys


@pytest.mark.asyncio
async def test_sqlite_store_query_states():
    """Test querying states with metadata."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        store = SQLiteStore(str(db_path))

        # Create states with different iterations and modes
        state1 = AgentState(query="query1", user_id="query_user1")
        state1.execution.iteration = 5
        state1.execution.mode = "fast"

        state2 = AgentState(query="query2", user_id="query_user2")
        state2.execution.iteration = 10
        state2.execution.mode = "deep"

        await store.save("query_user1:default", state1)
        await store.save("query_user2:default", state2)

        # Query all states
        all_states = await store.query_states()
        assert len(all_states) >= 2

        # Query with iteration filter
        high_iteration_states = await store.query_states(min_iteration=8)
        matching_states = [
            s for s in high_iteration_states if s["user_id"] in ["query_user1", "query_user2"]
        ]
        assert len(matching_states) == 1
        assert matching_states[0]["user_id"] == "query_user2"

        # Query with mode filter
        fast_states = await store.query_states(mode="fast")
        matching_fast = [s for s in fast_states if s["user_id"] == "query_user1"]
        assert len(matching_fast) == 1


@pytest.mark.asyncio
async def test_sqlite_store_concurrent_access():
    """Test concurrent read/write operations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "concurrent.db"

        # Create multiple store instances (simulating concurrent access)
        store1 = SQLiteStore(str(db_path))
        store2 = SQLiteStore(str(db_path))

        # Concurrent writes
        state1 = AgentState(query="concurrent1", user_id="concurrent_user1")
        state2 = AgentState(query="concurrent2", user_id="concurrent_user2")

        import asyncio

        results = await asyncio.gather(
            store1.save("concurrent_user1:default", state1),
            store2.save("concurrent_user2:default", state2),
        )

        assert all(results)  # Both saves should succeed

        # Concurrent reads
        loaded_states = await asyncio.gather(
            store1.load("concurrent_user1:default"), store2.load("concurrent_user2:default")
        )

        assert loaded_states[0] is not None
        assert loaded_states[1] is not None
        assert loaded_states[0]["state"]["execution"]["query"] == "concurrent1"
        assert loaded_states[1]["state"]["execution"]["query"] == "concurrent2"


@pytest.mark.asyncio
async def test_sqlite_store_schema_evolution():
    """Test that the store handles schema creation properly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "schema.db"

        # First store instance creates schema
        store1 = SQLiteStore(str(db_path))
        state = AgentState(query="schema test", user_id="schema_user")
        success = await store1.save("schema_user:default", state)
        assert success is True

        # Second store instance uses existing schema
        store2 = SQLiteStore(str(db_path))
        loaded = await store2.load("schema_user:default")
        assert loaded is not None
        assert loaded["state"]["execution"]["query"] == "schema test"
