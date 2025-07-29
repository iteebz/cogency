"""Test notification system core logic."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from cogency.utils.notify import (
    Notification,
    NotificationFormatter,
    NotificationStream,
    Notifier,
    Phase,
)


def test_notification_dataclass():
    """Test notification dataclass structure."""
    notification = Notification(
        phase="reason", message="Processing query", metadata={"iteration": 1}
    )

    assert notification.phase == "reason"
    assert notification.message == "Processing query"
    assert notification.metadata == {"iteration": 1}


def test_notifier_phase_methods():
    """Test notifier phase-specific methods."""
    notifier = Notifier(verbose=True, trace=True)

    notifier.preprocess("Analyzing query")
    notifier.reason("Thinking about solution")
    notifier.action("Executing tool")
    notifier.respond("Generating response")
    notifier.trace("Debug info", {"step": "parsing"})

    assert len(notifier.notifications) == 5
    assert notifier.notifications[0].phase == "preprocess"
    assert notifier.notifications[1].phase == "reason"
    assert notifier.notifications[2].phase == "action"
    assert notifier.notifications[3].phase == "respond"
    assert notifier.notifications[4].phase == "trace"


def test_notifier_trace_filtering():
    """Test trace notifications are filtered when trace=False."""
    notifier = Notifier(trace=False, verbose=True)

    notifier.reason("Normal message")
    notifier.trace("Debug message")

    assert len(notifier.notifications) == 1
    assert notifier.notifications[0].phase == "reason"


def test_notifier_verbose_filtering():
    """Test verbose notifications are filtered when verbose=False."""
    notifier = Notifier(trace=True, verbose=False)

    notifier.reason("Normal message")
    notifier.trace("Debug message")

    assert len(notifier.notifications) == 1
    assert notifier.notifications[0].phase == "trace"


@pytest.mark.asyncio
async def test_notifier_callback():
    """Test notifier callback mechanism."""
    callback = AsyncMock()
    notifier = Notifier(callback=callback, verbose=True)

    notifier.reason("Test message", {"key": "value"})

    # Allow async task to complete
    await asyncio.sleep(0.01)

    callback.assert_called_once_with("reason", "Test message", {"key": "value"})


def test_formatter_emoji_formatting():
    """Test notification formatter with emojis."""
    notification = Notification("reason", "Thinking", {})

    formatted = NotificationFormatter.format(notification, include_emoji=True)
    assert formatted == "💭 Thinking"

    formatted_no_emoji = NotificationFormatter.format(notification, include_emoji=False)
    assert formatted_no_emoji == "Thinking"


def test_formatter_thinking():
    """Test thinking formatter."""
    fast_thinking = NotificationFormatter.format_thinking("Quick thought", "fast")
    assert fast_thinking == "💭 Quick thought"

    deep_thinking = NotificationFormatter.format_thinking("Deep analysis", "deep")
    assert deep_thinking == "🧠 Deep analysis"

    empty_thinking = NotificationFormatter.format_thinking(None)
    assert empty_thinking == "Processing request..."


def test_stream_get_by_phase():
    """Test notification stream phase filtering."""
    notifier = Notifier(verbose=True, trace=True)
    notifier.reason("First thought")
    notifier.action("Execute tool")
    notifier.reason("Second thought")

    stream = NotificationStream(notifier)
    reason_notifications = stream.get_by_phase(Phase.REASON)

    assert len(reason_notifications) == 2
    assert all(n.phase == "reason" for n in reason_notifications)


@pytest.mark.asyncio
async def test_stream_formatting():
    """Test notification stream formatting."""
    notifier = Notifier(verbose=True)
    notifier.action("Tool executed")
    notifier.respond("Response generated")

    stream = NotificationStream(notifier)
    formatted = [msg async for msg in stream.stream(include_emoji=True)]

    assert len(formatted) == 2
    assert formatted[0] == "⚡ Tool executed"
    assert formatted[1] == "🤖 Response generated"
