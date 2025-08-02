"""End-to-end memory lifecycle tests - cross-session continuity."""

from unittest.mock import AsyncMock

import pytest

from cogency import Agent, MemoryConfig
from cogency.persist.store.filesystem import Filesystem
from tests.fixtures.llm import MockLLM


def create_memory_agent(name="test", **kwargs):
    """Helper to create Agent with memory config."""
    # Extract tools, defaulting to empty list
    tools = kwargs.pop("tools", [])

    # Create agent directly with new constructor
    return Agent(name, tools=tools, **kwargs)


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
    agent1 = create_memory_agent("test", llm=synthesis_llm, memory=memory_config)

    # User provides preferences
    memory1 = await agent1.memory()
    await memory1.remember("I prefer TypeScript over JavaScript", human=True)
    await memory1.remember("I'm working on a React project", human=True)

    # Force synthesis
    long_content = "Additional context " * 20  # Force over threshold
    await memory1.remember(long_content, human=True)

    # Verify synthesis occurred and persisted
    assert memory1.impression != ""
    assert memory1.recent == ""  # Cleared after synthesis

    # Session 2: New agent instance loads existing memory
    agent2 = create_memory_agent("test", llm=MockLLM(), memory=memory_config)
    memory2 = await agent2.memory()

    # Load should happen automatically in Agent.__init__ for configured memory
    success = await memory2.load()
    assert success is True

    # Verify continuity
    assert memory2.impression == memory1.impression
    assert "TypeScript" in memory2.impression or "React" in memory2.impression

    # Session 2: Add new information and save it
    await memory2.remember("I also like using Tailwind CSS", human=True)
    await memory2.save()  # Save the recent addition

    # Session 3: Verify accumulated memory
    agent3 = create_memory_agent("test", llm=MockLLM(), memory=memory_config)
    memory3 = await agent3.memory()
    await memory3.load()

    memory_context = await memory3.recall()
    assert "TypeScript" in memory_context or "React" in memory_context
    # Tailwind should be in recent interactions since it was saved
    assert "Tailwind" in memory3.recent


@pytest.mark.asyncio
async def test_memory_multi_user_isolation():
    """Test memory isolation between different users."""
    store = Filesystem(base_dir=".cogency/memory")

    # User 1 memory
    memory_config_1 = MemoryConfig(user_id="user_1", store=store)
    agent1 = create_memory_agent("test", llm=MockLLM(), memory=memory_config_1)
    memory1 = await agent1.memory()
    await memory1.remember("User 1 prefers Python", human=True)
    await memory1.save()

    # User 2 memory
    memory_config_2 = MemoryConfig(user_id="user_2", store=store)
    agent2 = create_memory_agent("test", llm=MockLLM(), memory=memory_config_2)
    memory2 = await agent2.memory()
    await memory2.remember("User 2 prefers Go", human=True)
    await memory2.save()

    # Verify isolation - User 1 cannot see User 2's memory
    agent1_reload = create_memory_agent("test", llm=MockLLM(), memory=memory_config_1)
    memory1_reload = await agent1_reload.memory()
    await memory1_reload.load()
    user1_context = await memory1_reload.recall()

    assert "Python" in user1_context
    assert "Go" not in user1_context

    # Verify isolation - User 2 cannot see User 1's memory
    agent2_reload = create_memory_agent("test", llm=MockLLM(), memory=memory_config_2)
    memory2_reload = await agent2_reload.memory()
    await memory2_reload.load()
    user2_context = await memory2_reload.recall()

    assert "Go" in user2_context
    assert "Python" not in user2_context


@pytest.mark.asyncio
async def test_memory_config_integration():
    """Test memory configuration integration with Agent."""
    # Test union pattern: bool vs MemoryConfig

    # Simple boolean (existing pattern)
    agent_simple = create_memory_agent("test", llm=MockLLM(), memory=True)
    memory_simple = await agent_simple.memory()
    assert memory_simple is not None
    assert memory_simple.synthesis_threshold == 16000  # Default

    # Advanced config
    memory_config = MemoryConfig(synthesis_threshold=5000, user_id="config_test_user")
    agent_config = create_memory_agent("test", llm=MockLLM(), memory=memory_config)
    memory_advanced = await agent_config.memory()
    assert memory_advanced is not None
    assert memory_advanced.synthesis_threshold == 5000  # Configured
    assert memory_advanced.user_id == "config_test_user"

    # Disabled memory
    agent_disabled = create_memory_agent("test", llm=MockLLM(), memory=False)
    memory_disabled = await agent_disabled.memory()
    assert memory_disabled is None
