"""End-to-end memory lifecycle tests - cross-session continuity."""

from unittest.mock import AsyncMock

import pytest

from cogency import Agent, MemoryConfig
from cogency.persist.store.filesystem import Filesystem
from tests.conftest import MockLLM


@pytest.mark.asyncio
async def test_memory_session_continuity():
    """Test memory persists and continues across agent sessions."""
    # Setup shared store
    store = Filesystem(base_dir=".cogency/memory")
    memory_config = MemoryConfig(
        synthesis_threshold=100, user_id="test_user_continuity"  # Low threshold for testing
    )
    memory_config.store = store

    # Session 1: Agent learns user preferences with realistic synthesis response
    synthesis_llm = MockLLM(
        response="User prefers TypeScript over JavaScript and is working on a React project. Shows strong frontend development focus."
    )
    agent1 = Agent("test", llm=synthesis_llm, memory=memory_config)

    # User provides preferences
    await agent1.memory.remember("I prefer TypeScript over JavaScript", human=True)
    await agent1.memory.remember("I'm working on a React project", human=True)

    # Force synthesis
    long_content = "Additional context " * 20  # Force over threshold
    await agent1.memory.remember(long_content, human=True)

    # Verify synthesis occurred and persisted
    assert agent1.memory.impression != ""
    assert agent1.memory.recent == ""  # Cleared after synthesis

    # Session 2: New agent instance loads existing memory
    agent2 = Agent("test", llm=MockLLM(), memory=memory_config)

    # Load should happen automatically in Agent.__init__ for configured memory
    success = await agent2.memory.load()
    assert success is True

    # Verify continuity
    assert agent2.memory.impression == agent1.memory.impression
    assert "TypeScript" in agent2.memory.impression or "React" in agent2.memory.impression

    # Session 2: Add new information and save it
    await agent2.memory.remember("I also like using Tailwind CSS", human=True)
    await agent2.memory.save()  # Save the recent addition

    # Session 3: Verify accumulated memory
    agent3 = Agent("test", llm=MockLLM(), memory=memory_config)
    await agent3.memory.load()

    memory_context = await agent3.memory.recall()
    assert "TypeScript" in memory_context or "React" in memory_context
    # Tailwind should be in recent interactions since it was saved
    assert "Tailwind" in agent3.memory.recent


@pytest.mark.asyncio
async def test_memory_multi_user_isolation():
    """Test memory isolation between different users."""
    store = Filesystem(base_dir=".cogency/memory")

    # User 1 memory
    memory_config_1 = MemoryConfig(user_id="user_1", store=store)
    agent1 = Agent("test", llm=MockLLM(), memory=memory_config_1)
    await agent1.memory.remember("User 1 prefers Python", human=True)
    await agent1.memory.save()

    # User 2 memory
    memory_config_2 = MemoryConfig(user_id="user_2", store=store)
    agent2 = Agent("test", llm=MockLLM(), memory=memory_config_2)
    await agent2.memory.remember("User 2 prefers Go", human=True)
    await agent2.memory.save()

    # Verify isolation - User 1 cannot see User 2's memory
    agent1_reload = Agent("test", llm=MockLLM(), memory=memory_config_1)
    await agent1_reload.memory.load()
    user1_context = await agent1_reload.memory.recall()

    assert "Python" in user1_context
    assert "Go" not in user1_context

    # Verify isolation - User 2 cannot see User 1's memory
    agent2_reload = Agent("test", llm=MockLLM(), memory=memory_config_2)
    await agent2_reload.memory.load()
    user2_context = await agent2_reload.memory.recall()

    assert "Go" in user2_context
    assert "Python" not in user2_context


@pytest.mark.asyncio
async def test_memory_config_integration():
    """Test memory configuration integration with Agent."""
    # Test union pattern: bool vs MemoryConfig

    # Simple boolean (existing pattern)
    agent_simple = Agent("test", llm=MockLLM(), memory=True)
    assert agent_simple.memory is not None
    assert agent_simple.memory.synthesis_threshold == 16000  # Default

    # Advanced config
    memory_config = MemoryConfig(synthesis_threshold=5000, user_id="config_test_user")
    agent_config = Agent("test", llm=MockLLM(), memory=memory_config)

    assert agent_config.memory is not None
    assert agent_config.memory.synthesis_threshold == 5000  # Configured
    assert agent_config.memory.user_id == "config_test_user"

    # Disabled memory
    agent_disabled = Agent("test", llm=MockLLM(), memory=False)
    assert agent_disabled.memory is None
