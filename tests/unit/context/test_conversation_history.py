"""Tests for conversation history functionality"""

import pytest
from unittest.mock import AsyncMock

from cogency.agent import Agent
from cogency.context import Context
from cogency.llm.mock import MockLLM
from cogency.memory.filesystem import FSMemory


class TestConversationHistory:
    """Test conversation history management"""

    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM for testing"""
        llm = MockLLM()
        llm.response = "Test response"
        return llm

    @pytest.fixture
    def fs_memory(self, tmp_path):
        """Create temporary filesystem memory"""
        return FSMemory(str(tmp_path))

    @pytest.fixture
    def agent_with_history(self, mock_llm, fs_memory):
        """Create agent with conversation history enabled"""
        return Agent(
            name="test_agent",
            llm=mock_llm,
            memory=fs_memory,
            conversation_history=True,
            max_history=3
        )

    @pytest.fixture
    def agent_without_history(self, mock_llm, fs_memory):
        """Create agent with conversation history disabled"""
        return Agent(
            name="test_agent", 
            llm=mock_llm,
            memory=fs_memory,
            conversation_history=False
        )

    @pytest.mark.asyncio
    async def test_conversation_history_enabled(self, agent_with_history):
        """Test that conversation history is stored when enabled"""
        # First query
        response1 = await agent_with_history.run("Hello", user_id="user1")
        assert response1 == "Test response"
        
        # Check history is stored
        context = agent_with_history.user_contexts["user1"]
        assert len(context.conversation_history) == 1
        assert context.conversation_history[0]["query"] == "Hello"
        assert context.conversation_history[0]["response"] == "Test response"

    @pytest.mark.asyncio
    async def test_conversation_history_disabled(self, agent_without_history):
        """Test that conversation history is not stored when disabled"""
        response = await agent_without_history.run("Hello", user_id="user1")
        assert response == "Test response"
        
        # No user contexts should be created
        assert len(agent_without_history.user_contexts) == 0

    @pytest.mark.asyncio
    async def test_user_isolation(self, agent_with_history):
        """Test that different users have isolated conversation histories"""
        # User 1 queries
        await agent_with_history.run("Hello from user 1", user_id="user1")
        await agent_with_history.run("Second query from user 1", user_id="user1")
        
        # User 2 queries
        await agent_with_history.run("Hello from user 2", user_id="user2")
        
        # Check isolation
        user1_context = agent_with_history.user_contexts["user1"]
        user2_context = agent_with_history.user_contexts["user2"]
        
        assert len(user1_context.conversation_history) == 2
        assert len(user2_context.conversation_history) == 1
        
        assert user1_context.conversation_history[0]["query"] == "Hello from user 1"
        assert user2_context.conversation_history[0]["query"] == "Hello from user 2"

    @pytest.mark.asyncio
    async def test_backward_compatibility_no_user_id(self, agent_with_history):
        """Test backward compatibility when no user_id is provided"""
        response = await agent_with_history.run("Hello")
        assert response == "Test response"
        
        # Should use "default" as user_id
        assert "default" in agent_with_history.user_contexts
        context = agent_with_history.user_contexts["default"]
        assert len(context.conversation_history) == 1
        assert context.conversation_history[0]["query"] == "Hello"

    @pytest.mark.asyncio
    async def test_rolling_window_history(self, agent_with_history):
        """Test that rolling window limits conversation history"""
        # Add more conversations than max_history (3)
        for i in range(5):
            await agent_with_history.run(f"Query {i}", user_id="user1")
        
        # Should only keep last 3 conversations
        context = agent_with_history.user_contexts["user1"]
        assert len(context.conversation_history) == 3
        assert context.conversation_history[0]["query"] == "Query 2"
        assert context.conversation_history[1]["query"] == "Query 3"
        assert context.conversation_history[2]["query"] == "Query 4"

    @pytest.mark.asyncio
    async def test_clear_conversation_history(self, agent_with_history):
        """Test clearing conversation history"""
        # Add some history
        await agent_with_history.run("Hello", user_id="user1")
        await agent_with_history.run("How are you?", user_id="user1")
        
        # Verify history exists
        context = agent_with_history.user_contexts["user1"]
        assert len(context.conversation_history) == 2
        
        # Clear history
        agent_with_history.clear_conversation_history(user_id="user1")
        
        # Verify history is cleared
        assert len(context.conversation_history) == 0

    @pytest.mark.asyncio
    async def test_get_conversation_history(self, agent_with_history):
        """Test retrieving conversation history"""
        # Add some history
        await agent_with_history.run("Hello", user_id="user1")
        await agent_with_history.run("How are you?", user_id="user1")
        await agent_with_history.run("What's the weather?", user_id="user1")
        
        # Get recent history
        context = agent_with_history.user_contexts["user1"]
        recent_history = agent_with_history.get_conversation_history(context, n=2)
        
        assert len(recent_history) == 2
        assert recent_history[0]["query"] == "How are you?"
        assert recent_history[1]["query"] == "What's the weather?"

    @pytest.mark.asyncio
    async def test_context_persistence_across_calls(self, agent_with_history):
        """Test that context persists across multiple calls for same user"""
        # First call
        await agent_with_history.run("Hello", user_id="user1")
        context1 = agent_with_history.user_contexts["user1"]
        
        # Second call - should reuse same context
        await agent_with_history.run("Follow up", user_id="user1")
        context2 = agent_with_history.user_contexts["user1"]
        
        # Should be same context object
        assert context1 is context2
        assert len(context1.conversation_history) == 2