"""Integration tests for multitenancy isolation and user_id scoping."""

from cogency.state import Conversation, Workspace
from cogency.storage import SQLite


class TestMultitenancyIsolation:
    """Core multitenancy isolation tests."""

    async def test_conversation_isolation(self):
        """Test that conversations are isolated by user_id."""
        store = SQLite()
        await store._ensure_schema()

        # Create conversations for different users
        user1_conv = Conversation(
            conversation_id="conv1",
            user_id="user1",
            messages=[{"role": "user", "content": "Python help"}],
        )

        user2_conv = Conversation(
            conversation_id="conv2",
            user_id="user2",
            messages=[{"role": "user", "content": "JavaScript help"}],
        )

        await store.save_conversation(user1_conv)
        await store.save_conversation(user2_conv)

        # Load as correct user - should succeed
        loaded_user1 = await store.load_conversation("conv1", "user1")
        assert loaded_user1 is not None
        assert loaded_user1.user_id == "user1"
        assert "Python" in loaded_user1.messages[0]["content"]

        loaded_user2 = await store.load_conversation("conv2", "user2")
        assert loaded_user2 is not None
        assert loaded_user2.user_id == "user2"
        assert "JavaScript" in loaded_user2.messages[0]["content"]

        # Cross-user access should fail
        cross_access1 = await store.load_conversation("conv1", "user2")
        assert cross_access1 is None

        cross_access2 = await store.load_conversation("conv2", "user1")
        assert cross_access2 is None

    async def test_workspace_isolation(self):
        """Test that workspaces are isolated by user_id."""
        store = SQLite()
        await store._ensure_schema()

        # Create workspaces for different users
        user1_workspace = Workspace(
            objective="Build Python API",
            insights=["Use FastAPI framework", "Implement authentication"],
        )

        user2_workspace = Workspace(
            objective="Create React app", insights=["Use TypeScript", "Implement routing"]
        )

        # Save workspaces with user-specific task IDs
        await store.save_workspace("task1", "user1", user1_workspace)
        await store.save_workspace("task2", "user2", user2_workspace)

        # Load as correct user - should succeed
        loaded_user1 = await store.load_workspace("task1", "user1")
        assert loaded_user1 is not None
        assert loaded_user1.objective == "Build Python API"
        assert "FastAPI" in loaded_user1.insights[0]

        loaded_user2 = await store.load_workspace("task2", "user2")
        assert loaded_user2 is not None
        assert loaded_user2.objective == "Create React app"
        assert "TypeScript" in loaded_user2.insights[0]

        # Cross-user access should fail
        cross_access1 = await store.load_workspace("task1", "user2")
        assert cross_access1 is None

        cross_access2 = await store.load_workspace("task2", "user1")
        assert cross_access2 is None


class TestMultitenancyRuntimeInjection:
    """Runtime user_id injection and propagation tests."""

    async def test_agent_run_user_id_propagation(self):
        """Test that user_id is properly propagated through agent.run_async."""
        from unittest.mock import patch

        from cogency import Agent

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            agent = Agent("test", memory=False)  # No memory to avoid complex setup

            # Should not crash and should handle user_id parameter
            result = await agent.run_async("Simple query", user_id="test_user")
            assert isinstance(result, str)
            assert len(result) > 0

    async def test_memory_activate_user_id_injection(self):
        """Test memory activation with user_id injection."""
        from cogency.memory import Memory

        memory = Memory()

        # Should handle user_id scoping without errors
        context = await memory.activate("Test query", user_id="test_user")
        assert isinstance(context, str)
        # Context should be empty or contain user info, but not crash
