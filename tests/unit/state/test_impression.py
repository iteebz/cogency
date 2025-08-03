"""Memory system tests - UserProfile and ImpressionSynthesizer."""

from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from cogency.memory import ImpressionSynthesizer
from cogency.state.user_profile import UserProfile


@pytest.fixture
def mock_llm():
    """Mock LLM for testing."""
    llm = Mock()
    return llm


@pytest.fixture
def mock_store():
    """Mock store for testing."""
    store = AsyncMock()
    return store


@pytest.fixture
def synthesizer(mock_llm, mock_store):
    """ImpressionSynthesizer instance for testing."""
    return ImpressionSynthesizer(llm=mock_llm, store=mock_store)


def test_constructor(mock_llm, mock_store):
    """Test ImpressionSynthesizer constructor."""
    synthesizer = ImpressionSynthesizer(llm=mock_llm, store=mock_store)

    assert synthesizer.llm is mock_llm
    assert synthesizer.store is mock_store
    assert synthesizer.synthesis_threshold == 3


@pytest.mark.asyncio
async def test_load_profile_new_user(synthesizer, mock_store):
    """Test loading profile for new user."""
    mock_store.load.return_value = None

    profile = await synthesizer._load_profile("new_user")

    assert profile.user_id == "new_user"
    assert profile.interaction_count == 0
    mock_store.load.assert_called_once_with("profile:new_user")


@pytest.mark.asyncio
async def test_load_existing(synthesizer, mock_store):
    """Test loading existing user profile."""
    existing_data = {
        "state": {
            "user_id": "existing_user",
            "interaction_count": 5,
            "preferences": {"format": "json"},
            "created_at": "2023-01-01T00:00:00",
            "last_updated": "2023-01-02T00:00:00",
        }
    }
    mock_store.load.return_value = existing_data

    profile = await synthesizer._load_profile("existing_user")

    assert profile.user_id == "existing_user"
    assert profile.interaction_count == 5
    assert profile.preferences["format"] == "json"
    assert isinstance(profile.created_at, datetime)
    assert isinstance(profile.last_updated, datetime)


@pytest.mark.asyncio
async def test_save_profile(synthesizer, mock_store):
    """Test saving profile to store."""
    profile = UserProfile(user_id="test_user")
    profile.preferences = {"format": "json"}

    await synthesizer._save_profile(profile)

    mock_store.save.assert_called_once()
    call_args = mock_store.save.call_args
    assert call_args[0][0] == "profile:test_user"
    saved_data = call_args[0][1]
    assert saved_data["user_id"] == "test_user"
    assert saved_data["preferences"] == {"format": "json"}
    assert "created_at" in saved_data
    assert "last_updated" in saved_data


@pytest.mark.asyncio
async def test_extract_success(synthesizer, mock_llm):
    """Test extracting insights from interaction."""
    mock_result = Mock()
    mock_result.success = True
    mock_result.data = '{"preferences": {"format": "json"}, "goals": ["test goal"]}'

    # Make the mock async
    from unittest.mock import AsyncMock

    mock_llm.run = AsyncMock(return_value=mock_result)

    interaction_data = {"query": "test query", "response": "test response", "success": True}

    from cogency.memory.insights import extract_insights

    insights = await extract_insights(mock_llm, interaction_data)

    assert insights["preferences"]["format"] == "json"
    assert "test goal" in insights["goals"]
    mock_llm.run.assert_called_once()


@pytest.mark.asyncio
async def test_extract_failure(synthesizer, mock_llm):
    """Test handling LLM failure in insight extraction."""
    mock_result = Mock()
    mock_result.success = False

    # Make the mock async
    from unittest.mock import AsyncMock

    mock_llm.run = AsyncMock(return_value=mock_result)

    interaction_data = {"query": "test", "response": "test", "success": True}

    from cogency.memory.insights import extract_insights

    insights = await extract_insights(mock_llm, interaction_data)

    assert insights == {}


@pytest.mark.asyncio
async def test_synthesize_profile(synthesizer, mock_llm):
    """Test profile synthesis."""
    profile = UserProfile(user_id="test_user")
    profile.preferences = {"old": "preference"}

    mock_result = Mock()
    mock_result.success = True
    mock_result.data = '{"preferences": {"new": "preference"}, "goals": ["synthesized goal"]}'

    # Make the mock async
    from unittest.mock import AsyncMock

    mock_llm.run = AsyncMock(return_value=mock_result)

    recent_interaction = {"query": "test", "success": True}

    result_profile = await synthesizer._synthesize_profile(profile, recent_interaction)

    assert result_profile.synthesis_version == 2
    mock_llm.run.assert_called_once()


@pytest.mark.asyncio
async def test_update_no_synthesis(synthesizer, mock_llm, mock_store):
    """Test updating impression without synthesis threshold."""
    # Mock profile loading
    mock_store.load.return_value = None

    # Mock insight extraction
    mock_result = Mock()
    mock_result.success = True
    mock_result.data = '{"preferences": {"format": "json"}}'

    # Make the mock async
    from unittest.mock import AsyncMock

    mock_llm.run = AsyncMock(return_value=mock_result)

    interaction_data = {"query": "test", "response": "test", "success": True}

    profile = await synthesizer.update_impression("test_user", interaction_data)

    assert profile.user_id == "test_user"
    assert profile.interaction_count == 1
    assert profile.preferences["format"] == "json"
    # Should not synthesize (count=1, threshold=3)
    assert profile.synthesis_version == 1


@pytest.mark.asyncio
async def test_update_with_synthesis(synthesizer, mock_llm, mock_store):
    """Test updating impression with synthesis."""
    # Mock existing profile at synthesis threshold
    existing_data = {
        "state": {
            "user_id": "test_user",
            "interaction_count": 2,  # Will become 3 after update
            "synthesis_version": 1,
            "created_at": "2023-01-01T00:00:00",
            "last_updated": "2023-01-02T00:00:00",
        }
    }
    mock_store.load.return_value = existing_data

    # Mock insight extraction and synthesis
    mock_result = Mock()
    mock_result.success = True
    mock_result.data = '{"preferences": {"format": "json"}}'

    # Make the mock async
    from unittest.mock import AsyncMock

    mock_llm.run = AsyncMock(return_value=mock_result)

    interaction_data = {"query": "test", "response": "test", "success": True}

    profile = await synthesizer.update_impression("test_user", interaction_data)

    assert profile.interaction_count == 3
    # Should trigger synthesis (3 % 3 == 0)
    assert mock_llm.run.call_count == 2  # Once for extraction, once for synthesis
    mock_store.save.assert_called_once()
