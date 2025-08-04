"""End-to-end memory lifecycle tests - cross-session continuity."""

from unittest.mock import AsyncMock, patch

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
    """Test ImpressionSynthesizer persists user profiles across sessions."""
    with patch("cogency.events.core._bus", None):  # Disable event system
        from cogency.memory import ImpressionSynthesizer
        from tests.fixtures.store import InMemoryStore

        # Setup shared store and synthesizer
        store = InMemoryStore()
        synthesis_llm = MockLLM(
            response='{"preferences": {"language": "TypeScript"}, "goals": ["React development"], "expertise": ["frontend"]}'
        )
        synthesizer = ImpressionSynthesizer(synthesis_llm, store=store)
        synthesizer.synthesis_threshold = 1  # Synthesize every interaction

        user_id = "test_user_continuity"

        # Session 1: Process user preferences
        interaction1 = {
            "query": "I prefer TypeScript over JavaScript",
            "response": "I'll help with TypeScript",
            "success": True,
        }
        profile1 = await synthesizer.update_impression(user_id, interaction1)

        # Verify profile was created and synthesized
        assert profile1.user_id == user_id
        assert profile1.interaction_count == 1

        # Session 2: Load existing profile and add new interaction
        interaction2 = {
            "query": "I'm working on a React project",
            "response": "Great! I can help with React",
            "success": True,
        }
        profile2 = await synthesizer.update_impression(user_id, interaction2)

        # Verify continuity - same user_id should load existing profile
        assert profile2.user_id == user_id
        assert profile2.interaction_count == 2  # Incremented from first session

        # Session 3: Verify profile contains accumulated understanding
        profile3 = await synthesizer._load_profile(user_id)
        from cogency.memory.compression import compress

        context = compress(profile3)

        # Should contain learned information from both sessions
        assert profile3.interaction_count >= 2
        assert len(context) > 0  # Has some context to inject


@pytest.mark.asyncio
async def test_memory_multi_user_isolation():
    """Test ImpressionSynthesizer isolates profiles between users."""
    with patch("cogency.events.core._bus", None):  # Disable event system
        from cogency.memory import ImpressionSynthesizer
        from tests.fixtures.store import InMemoryStore

        # Shared store and synthesizer
        store = InMemoryStore()
        synthesis_llm = MockLLM(
            response='{"preferences": {"language": "Python"}, "expertise": ["backend"]}'
        )
        synthesizer = ImpressionSynthesizer(synthesis_llm, store=store)

        # User 1 interaction
        user1_interaction = {
            "query": "I prefer Python for backend development",
            "response": "I'll help with Python",
            "success": True,
        }
        profile1 = await synthesizer.update_impression("user_1", user1_interaction)

        # User 2 interaction with different LLM response
        synthesis_llm_user2 = MockLLM(
            response='{"preferences": {"language": "Go"}, "expertise": ["systems"]}'
        )
        synthesizer2 = ImpressionSynthesizer(synthesis_llm_user2, store=store)

        user2_interaction = {
            "query": "I prefer Go for systems programming",
            "response": "I'll help with Go",
            "success": True,
        }
        profile2 = await synthesizer2.update_impression("user_2", user2_interaction)

        # Verify isolation
        assert profile1.user_id == "user_1"
        assert profile2.user_id == "user_2"

        # Reload profiles to verify persistence isolation
        reloaded_profile1 = await synthesizer._load_profile("user_1")
        reloaded_profile2 = await synthesizer._load_profile("user_2")

        assert reloaded_profile1.user_id == "user_1"
        assert reloaded_profile2.user_id == "user_2"

        # Verify context isolation
        from cogency.memory.compression import compress

        context1 = compress(reloaded_profile1)
        context2 = compress(reloaded_profile2)

        # Each user should have their own context
        assert context1 != context2


@pytest.mark.asyncio
async def test_memory_config_integration():
    """Test AgentState integration with UserProfile."""
    from cogency.state import AgentState, UserProfile

    # Test AgentState without user profile
    state_no_profile = AgentState(query="test query", user_id="test_user")
    context_no_profile = state_no_profile.get_situated_context()
    assert context_no_profile == ""  # No profile means no context

    # Test AgentState with user profile
    profile = UserProfile(user_id="test_user")
    profile.preferences = {"language": "Python"}
    profile.goals = ["Learn backend development"]
    profile.communication_style = "concise"

    state_with_profile = AgentState(query="test query", user_id="test_user", user_profile=profile)

    context_with_profile = state_with_profile.get_situated_context()
    assert "USER CONTEXT:" in context_with_profile
    assert "Python" in context_with_profile  # From preferences
    assert "concise" in context_with_profile  # From communication style

    # Test profile compression
    from cogency.memory.compression import compress

    compressed = compress(profile, max_tokens=100)
    assert len(compressed) <= 100
    assert "Python" in compressed
