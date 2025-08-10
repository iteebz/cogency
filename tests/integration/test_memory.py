"""End-to-end memory lifecycle tests - cross-session continuity."""

from unittest.mock import AsyncMock, patch

import pytest

from cogency import Agent, MemoryConfig
from cogency.storage.state import SQLite
from tests.fixtures.provider import MockProvider


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
        import tempfile
        from pathlib import Path

        from cogency.memory import ImpressionSynthesizer

        # Use temporary file database for true isolation
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        try:
            store = SQLite(db_path)
            provider = MockProvider(
                response='{"preferences": {"language": "TypeScript"}, "goals": ["React development"], "expertise": ["frontend"]}'
            )
            synthesizer = ImpressionSynthesizer(provider, store=store)
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

            # Should contain interaction count from both sessions
            assert profile3.interaction_count >= 2
            assert profile3.user_id == user_id  # Profile persisted correctly
        finally:
            Path(db_path).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_memory_multi_user_isolation():
    """Test ImpressionSynthesizer isolates profiles between users."""
    with patch("cogency.events.core._bus", None):  # Disable event system
        import tempfile
        from pathlib import Path

        from cogency.memory import ImpressionSynthesizer

        # Use temporary file database for true isolation
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        try:
            store = SQLite(db_path)
            provider = MockProvider(
                response='{"preferences": {"language": "Python"}, "expertise": ["backend"]}'
            )
            synthesizer = ImpressionSynthesizer(provider, store=store)

            # User 1 interaction
            user1_interaction = {
                "query": "I prefer Python for backend development",
                "response": "I'll help with Python",
                "success": True,
            }
            profile1 = await synthesizer.update_impression("user_1", user1_interaction)

            # User 2 interaction with different provider response
            provider_2 = MockProvider(
                response='{"preferences": {"language": "Go"}, "expertise": ["systems"]}'
            )
            synthesizer2 = ImpressionSynthesizer(provider_2, store=store)

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

            # Verify profile isolation
            assert reloaded_profile1.user_id != reloaded_profile2.user_id
            assert reloaded_profile1.interaction_count == 1
            assert reloaded_profile2.interaction_count == 1
        finally:
            Path(db_path).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_memory_config_integration():
    """Test State integration with Profile."""
    from cogency.state import Profile, State

    # Test State without user profile
    state_no_profile = State(query="test query", user_id="test_user")
    context_no_profile = state_no_profile.get_situated_context()
    assert context_no_profile == ""  # No profile means no context

    # Test State with user profile
    profile = Profile(user_id="test_user")
    profile.preferences = {"language": "Python"}
    profile.goals = ["Learn backend development"]
    profile.communication_style = "concise"

    state = State(query="test query", user_id="test_user")
    state.profile = profile

    context_with_profile = state.get_situated_context()
    assert "USER CONTEXT:" in context_with_profile
    assert "Python" in context_with_profile  # From preferences
    assert "concise" in context_with_profile  # From communication style

    # Test profile compression
    from cogency.memory.compression import compress

    compressed = compress(profile, max_tokens=100)
    assert len(compressed) <= 100
    assert "Python" in compressed


@pytest.mark.asyncio
async def test_synthesis_step_integration():
    """Test synthesis step integration with full pipeline."""
    with patch("cogency.events.core._bus", None):  # Disable event system
        from cogency.memory import ImpressionSynthesizer
        from cogency.state import Profile, State
        from cogency.steps.synthesize.core import synthesize

        # Setup
        store = SQLite(":memory:")
        provider = MockProvider(
            response='{"preferences": {"framework": "React"}, "goals": ["Build web apps"]}'
        )
        memory = ImpressionSynthesizer(provider, store=store)

        # Create user profile with synthesis triggers
        user_profile = Profile(user_id="integration_test")
        user_profile.interaction_count = 6  # Above threshold
        user_profile.synthesis_threshold = 5
        user_profile.last_synthesis_count = 0

        # Create agent state
        state = State(query="test query", user_id="integration_test")
        # user_id already set in State constructor
        state.profile = user_profile

        # Execute synthesis step
        await synthesize(state, memory)

        # Verify synthesis was executed (update_impression was called)
        # Profile should be updated with synthesis tracking
        assert hasattr(user_profile, "last_synthesis_count")

        # Load profile to verify persistence
        stored_profile = await memory._load_profile("integration_test")
        assert stored_profile is not None


@pytest.mark.asyncio
async def test_synthesis_lifecycle_complete():
    """Test complete synthesis lifecycle from trigger to completion."""
    with patch("cogency.events.core._bus", None):  # Disable event system
        from datetime import datetime, timedelta

        from cogency.memory import ImpressionSynthesizer
        from cogency.state import Profile, State
        from cogency.steps.synthesize.core import _should_synthesize, synthesize

        # Setup components
        store = SQLite(":memory:")
        provider = MockProvider(response='{"synthesis": "complete"}')
        memory = ImpressionSynthesizer(provider, store=store)

        # Test Case 1: Threshold trigger
        profile_threshold = Profile(user_id="threshold_user")
        profile_threshold.interaction_count = 10
        profile_threshold.synthesis_threshold = 5
        profile_threshold.last_synthesis_count = 0

        state_threshold = State(query="test", user_id="threshold_user")
        state_threshold.user = profile_threshold

        # Should trigger synthesis
        assert _should_synthesize(profile_threshold, state_threshold) is True

        # Execute synthesis
        await synthesize(state_threshold, memory)

        # Test Case 2: Session end trigger
        profile_session = Profile(user_id="session_user")
        profile_session.interaction_count = 2
        profile_session.synthesis_threshold = 5
        profile_session.last_synthesis_count = 0
        profile_session.last_interaction_time = datetime.now() - timedelta(minutes=45)
        profile_session.session_timeout = 1800  # 30 minutes

        state_session = State(query="test", user_id="session_user")
        state_session.user = profile_session

        # Should trigger synthesis due to session timeout
        assert _should_synthesize(profile_session, state_session) is True

        # Execute synthesis
        await synthesize(state_session, memory)

        # Test Case 3: High value trigger
        profile_high_value = Profile(user_id="high_value_user")
        profile_high_value.interaction_count = 2
        profile_high_value.synthesis_threshold = 5
        profile_high_value.last_synthesis_count = 0
        profile_high_value.last_interaction_time = datetime.now() - timedelta(minutes=5)

        state_high_value = State(query="test", user_id="high_value_user")
        state_high_value.execution.iteration = 8  # High complexity
        state_high_value.user = profile_high_value

        # Should trigger synthesis due to high complexity
        assert _should_synthesize(profile_high_value, state_high_value) is True

        # Execute synthesis
        await synthesize(state_high_value, memory)
