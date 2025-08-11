"""Unit tests for SituatedMemory - critical business logic only."""

from unittest.mock import AsyncMock, Mock

import pytest

from cogency.memory.situate import SituatedMemory


@pytest.mark.asyncio
async def test_profile_increment_logic():
    """Test profile interaction count increments correctly - CORE BUSINESS LOGIC."""
    from cogency.state import Profile

    provider = Mock()
    store = Mock()

    # Create a profile that persists across calls
    profile = Profile(user_id="user")
    store.load_profile = AsyncMock(return_value=profile)
    store.save_profile = AsyncMock()

    memory = SituatedMemory(provider, store)
    interaction = {"query": "Test", "response": "Response", "success": True}

    # Test profile increment behavior - same profile instance returned each time
    profile1 = await memory.update_impression("user", interaction)
    assert profile1.interaction_count == 1

    profile2 = await memory.update_impression("user", interaction)
    assert profile2.interaction_count == 2

    profile3 = await memory.update_impression("user", interaction)
    assert profile3.interaction_count == 3


@pytest.mark.asyncio
async def test_synthesis_resilience():
    """Test profile updates continue even if synthesis fails - CRITICAL ERROR HANDLING."""
    provider = Mock()
    provider.run = AsyncMock(side_effect=Exception("LLM Error"))
    store = Mock()
    store.load_profile = AsyncMock(return_value=None)
    store.save_profile = AsyncMock()

    memory = SituatedMemory(provider, store)

    interaction = {"query": "Test", "response": "Response", "success": True}

    # Should not raise exception despite LLM failure
    profile = await memory.update_impression("user", interaction)

    assert profile.user_id == "user"
    assert profile.interaction_count == 1
