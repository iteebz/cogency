"""Simple integration tests for notification system functionality."""

from unittest.mock import AsyncMock

import pytest

from cogency.notify import (
    CLIFormatter,
    EmojiFormatter,
    Formatter,
    JSONFormatter,
    Notifier,
    setup_formatter,
)
from cogency.phases.preprocess import preprocess
from cogency.phases.respond import respond
from cogency.state import State


@pytest.mark.asyncio
async def test_phase_notifications_direct():
    """Test notifications work directly with phase functions."""
    formatter = EmojiFormatter()
    notifier = Notifier(formatter=formatter)

    # Mock dependencies
    mock_llm = AsyncMock()
    mock_llm.run.return_value.success = True
    mock_llm.run.return_value.data = "Mock response"

    # Create state
    state = State(query="Test query")

    # Test respond phase (simplest)
    await respond(state, notifier, mock_llm, [], identity="Test Agent")

    # Verify notifications were generated
    assert len(notifier.notifications) >= 1

    # Check for respond phase notifications (ultimate form uses direct event types)
    respond_notifications = [n for n in notifier.notifications if n.type == "respond"]
    assert len(respond_notifications) >= 1


@pytest.mark.asyncio
async def test_notification_formatter_integration():
    """Test notification formatter with real notifications."""
    formatter = EmojiFormatter()
    notifier = Notifier(formatter=formatter)

    # Generate some notifications using ultimate callable API
    await notifier("preprocess", state="analyzing")
    await notifier("reason", state="thinking")
    await notifier("tool", name="search", ok=True, result="Found results")
    await notifier("respond", state="generating")

    # Test formatting
    formatted_messages = []
    for notification in notifier.notifications:
        formatted = formatter.format(notification)
        if formatted:  # Skip None results from silent formatters
            formatted_messages.append(formatted)

    # Verify emoji formatting
    assert any("⚙️" in msg and "preprocess" in msg.lower() for msg in formatted_messages)
    assert any("💭" in msg and "reason" in msg.lower() for msg in formatted_messages)
    assert any("🔍" in msg and "search" in msg.lower() for msg in formatted_messages)
    assert any("🤖" in msg and "respond" in msg.lower() for msg in formatted_messages)


@pytest.mark.asyncio
async def test_callback_integration():
    """Test callback mechanism works with phase notifications."""
    callback_notifications = []

    async def test_callback(notification):
        callback_notifications.append(notification)

    formatter = CLIFormatter()
    notifier = Notifier(formatter=formatter, on_notify=test_callback)

    # Send notifications using ultimate callable API
    await notifier("preprocess", state="starting")
    await notifier("reason", state="fast")
    await notifier("tool", name="search", ok=True)

    # Allow async callbacks to complete
    import asyncio

    await asyncio.sleep(0.01)

    # Verify callbacks were triggered
    assert len(callback_notifications) == 3
    assert callback_notifications[0].type == "preprocess"
    assert callback_notifications[0].data["state"] == "starting"
    assert callback_notifications[1].type == "reason"
    assert callback_notifications[1].data["state"] == "fast"
    assert callback_notifications[2].type == "tool"


@pytest.mark.asyncio
async def test_silent_mode_integration():
    """Test silent mode works as expected."""
    # Silent formatter returns None for all notifications
    silent_formatter = setup_formatter("silent")
    notifier_silent = Notifier(formatter=silent_formatter)

    await notifier_silent("reason", state="thinking")
    await notifier_silent("trace", message="Debug message")

    # Notifications are stored but formatting returns None
    assert len(notifier_silent.notifications) == 2
    for notification in notifier_silent.notifications:
        formatted = silent_formatter.format(notification)
        assert formatted is None  # Silent mode returns None

    # Regular formatter should format both
    regular_formatter = EmojiFormatter()
    notifier_regular = Notifier(formatter=regular_formatter)

    await notifier_regular("reason", state="thinking")
    await notifier_regular("trace", message="Debug message")

    assert len(notifier_regular.notifications) == 2
    for notification in notifier_regular.notifications:
        formatted = regular_formatter.format(notification)
        assert formatted is not None  # Regular mode formats messages
