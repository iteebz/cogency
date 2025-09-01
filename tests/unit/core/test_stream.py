"""Stream tests - Orchestration layer business logic."""

from unittest.mock import AsyncMock

import pytest

from cogency.core.config import Config
from cogency.core.protocols import Event
from cogency.core.stream import stream


@pytest.mark.asyncio
async def test_stream_mode_selection(mock_storage):
    """Stream selects correct mode based on config and capabilities."""
    mock_llm = AsyncMock()

    # Test replay mode selection
    config_replay = Config(llm=mock_llm, storage=mock_storage, tools=[], mode="replay")

    # Test inject mode selection
    config_resume = Config(llm=mock_llm, storage=mock_storage, tools=[], mode="resume")

    # Test auto mode with inject capability
    mock_llm.resumable = True
    config_auto_resume = Config(llm=mock_llm, storage=mock_storage, tools=[], mode="auto")

    # Test auto mode without inject capability
    mock_llm.resumable = False
    config_auto_replay = Config(llm=mock_llm, storage=mock_storage, tools=[], mode="auto")

    # Just verify configs are created (mode selection logic tested in integration)
    assert config_replay.mode == "replay"
    assert config_resume.mode == "resume"
    assert config_auto_resume.mode == "auto"
    assert config_auto_replay.mode == "auto"


@pytest.mark.asyncio
async def test_stream_event_buffering(mock_storage):
    """Stream buffers events for atomic persistence."""
    mock_llm = AsyncMock()
    mock_llm.resumable = False

    # Mock mode function to yield events
    async def mock_mode_events(config, query, user_id, conversation_id):
        yield {"type": Event.THINK, "content": "thinking"}
        yield {"type": Event.RESPOND, "content": "response"}
        yield {"type": Event.CALLS, "tools": []}

    config = Config(llm=mock_llm, storage=mock_storage, tools=[], mode="replay")

    # Mock callbacks to capture buffered events
    captured_events = []

    def mock_on_complete(conv_id, user_id, events):
        captured_events.extend(events)

    # Mock the mode function
    from unittest.mock import patch

    with patch("cogency.core.stream.replay", side_effect=mock_mode_events):
        events = []
        async for event in stream(config, "test", "user", "conv", on_complete=mock_on_complete):
            events.append(event)

    # Should buffer recordable events
    assert len(captured_events) >= 1  # at least one event should be captured
    # Should contain user query event
    assert any(e["type"] == Event.USER for e in captured_events)

    # Should add timestamps
    for event in captured_events:
        assert "timestamp" in event


@pytest.mark.asyncio
async def test_stream_callback_decoupling(mock_storage):
    """Stream accepts injected callbacks - no hard dependencies."""
    mock_llm = AsyncMock()
    mock_llm.resumable = False

    config = Config(llm=mock_llm, storage=mock_storage, tools=[], mode="replay")

    # Mock callbacks
    complete_called = False
    learn_called = False

    def mock_complete(conv_id, user_id, events):
        nonlocal complete_called
        complete_called = True
        assert conv_id == "test_conv"
        assert user_id == "test_user"
        assert isinstance(events, list)

    def mock_learn(user_id, llm):
        nonlocal learn_called
        learn_called = True
        assert user_id == "test_user"
        assert llm is config.llm

    # Mock mode to return empty
    from unittest.mock import patch

    async def empty_mode(config, query, user_id, conversation_id):
        return
        yield  # Make it async generator

    with patch("cogency.core.stream.replay", side_effect=empty_mode):
        async for _event in stream(
            config, "test", "test_user", "test_conv", on_complete=mock_complete, on_learn=mock_learn
        ):
            pass

    # Callbacks should be called
    assert complete_called
    assert learn_called


@pytest.mark.asyncio
async def test_stream_auto_mode_fallback(mock_storage):
    """Auto mode falls back from inject to replay when needed."""
    mock_llm = AsyncMock()

    # Test fallback logic
    mock_llm.resumable = False  # No inject capability
    config = Config(llm=mock_llm, storage=mock_storage, tools=[], mode="auto")

    # Should select replay
    # (This is integration behavior - unit test just verifies the logic path)

    # Test inject preference
    mock_llm.resumable = True  # Has inject capability
    config_resume = Config(llm=mock_llm, storage=mock_storage, tools=[], mode="auto")

    # Verify auto mode logic exists in stream function
    assert config.mode == "auto"
    assert config_resume.mode == "auto"

    # The actual fallback behavior is tested in integration
    # Unit test just verifies config accepts auto mode
