import pytest
from unittest.mock import Mock

from cogency.agent import Agent
from cogency.context import Context
from cogency.llm.base import BaseLLM


class MockLLM(BaseLLM):
    """Mock LLM for testing."""
    
    async def invoke(self, messages, **kwargs):
        return "Mock response"


class TestAgentContext:
    def test_agent_context_property_initially_none(self):
        """Test that agent.context is None before running."""
        llm = MockLLM()
        agent = Agent("test", llm)
        
        assert agent.context is None

    @pytest.mark.asyncio
    async def test_agent_stores_context_after_run(self):
        """Test that agent stores context after running."""
        llm = MockLLM()
        agent = Agent("test", llm)
        
        result = await agent.run("test message")
        
        assert agent.context is not None
        assert agent.context.current_input == "test message"

    @pytest.mark.asyncio
    async def test_agent_run_with_custom_context(self):
        """Test agent.run with custom context."""
        llm = MockLLM()
        agent = Agent("test", llm)
        
        # Create custom context with history
        custom_context = Context("initial", max_history=5)
        custom_context.add_message("user", "previous message")
        custom_context.add_message("assistant", "previous response")
        
        result = await agent.run("new message", context=custom_context)
        
        # Agent should use the provided context
        assert agent.context is custom_context
        assert agent.context.current_input == "new message"
        assert len(agent.context.messages) >= 2  # Should contain previous messages

    @pytest.mark.asyncio
    async def test_context_reuse_across_runs(self):
        """Test reusing context across multiple agent runs."""
        llm = MockLLM()
        agent = Agent("test", llm)
        
        context = Context("first", max_history=10)
        
        # First run
        await agent.run("first message", context=context)
        first_message_count = len(context.messages)
        
        # Second run with same context
        await agent.run("second message", context=context)
        second_message_count = len(context.messages)
        
        # Should accumulate messages
        assert second_message_count > first_message_count
        assert agent.context is context

    @pytest.mark.asyncio
    async def test_context_sliding_window_with_agent(self):
        """Test that sliding window works when using context with agent."""
        llm = MockLLM()
        agent = Agent("test", llm)
        
        context = Context("test", max_history=3)
        
        # Pre-populate context to near limit
        context.add_message("user", "msg1")
        context.add_message("assistant", "resp1")
        
        # Run agent - should add more messages and trigger sliding window
        await agent.run("new message", context=context)
        
        # Should respect the sliding window limit
        assert len(context.messages) <= 3

    @pytest.mark.asyncio
    async def test_context_property_persists_between_calls(self):
        """Test that context property persists between property accesses."""
        llm = MockLLM()
        agent = Agent("test", llm)
        
        await agent.run("test message")
        
        # Multiple property accesses should return same object
        context1 = agent.context
        context2 = agent.context
        assert context1 is context2

    @pytest.mark.asyncio
    async def test_agent_updates_current_input_on_existing_context(self):
        """Test that agent updates current_input when reusing context."""
        llm = MockLLM()
        agent = Agent("test", llm)
        
        context = Context("original input")
        await agent.run("new input", context=context)
        
        assert context.current_input == "new input"
        assert agent.context.current_input == "new input"