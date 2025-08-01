"""Test v2 notification system core logic."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from cogency.notify import (
    CLIFormatter,
    EmojiFormatter,
    Formatter,
    JSONFormatter,
    Notification,
    Notifier,
    emit,
    setup_formatter,
)


def test_notification_dataclass():
    """Test v2 notification dataclass structure."""
    notification = Notification(
        type="phase", data={"phase": "reason", "mode": "thinking", "iteration": 1}
    )

    assert notification.type == "phase"
    assert notification.data["phase"] == "reason"
    assert notification.data["mode"] == "thinking"
    assert notification.data["iteration"] == 1
    assert notification.timestamp > 0


@pytest.mark.asyncio
async def test_notifier_ultimate_callable():
    """Test ultimate callable notifier methods."""
    formatter = EmojiFormatter()
    notifier = Notifier(formatter=formatter)

    await notifier("prepare", state="analyzing")
    await notifier("reason", state="thinking")
    await notifier("tool", name="search", ok=True, result="Found data")
    await notifier("respond", state="generating")
    await notifier("trace", message="Debug info", step="parsing")

    assert len(notifier.notifications) == 5
    assert notifier.notifications[0].type == "prepare"
    assert notifier.notifications[0].data["state"] == "analyzing"
    assert notifier.notifications[1].data["state"] == "thinking"
    assert notifier.notifications[2].type == "tool"
    assert notifier.notifications[3].data["state"] == "generating"
    assert notifier.notifications[4].type == "trace"


@pytest.mark.asyncio
async def test_notifier_silent_mode():
    """Test silent mode returns None for all formatting."""
    silent_formatter = setup_formatter(notify=False, debug=False, style="silent")
    notifier = Notifier(formatter=silent_formatter)

    await notifier("reason", state="thinking")
    await notifier("trace", message="Debug message")

    # Notifications are stored but formatting returns None
    assert len(notifier.notifications) == 2
    for notification in notifier.notifications:
        formatted = silent_formatter.format(notification)
        assert formatted is None


@pytest.mark.asyncio
async def test_notifier_callback():
    """Test v2 notifier callback mechanism."""
    callback = AsyncMock()
    formatter = CLIFormatter()
    notifier = Notifier(formatter=formatter, on_notify=callback)

    await notifier("reason", state="thinking", content="Test message")

    # Allow async task to complete
    await asyncio.sleep(0.01)

    callback.assert_called_once()
    call_args = callback.call_args[0][0]  # First argument (notification)
    assert call_args.type == "reason"
    assert call_args.data["state"] == "thinking"


def test_cli_formatter():
    """Test CLI formatter output."""
    formatter = CLIFormatter()

    # Direct event notification
    reason_notification = Notification("reason", {"state": "thinking"})
    formatted = formatter.format(reason_notification)
    assert formatted == "Reason thinking"

    # Tool execution success
    tool_success = Notification("tool", {"name": "search", "ok": True, "result": "data"})
    formatted = formatter.format(tool_success)
    assert formatted == "search: data"

    # Tool execution failure
    tool_failure = Notification("tool", {"name": "search", "ok": False, "error": "timeout"})
    formatted = formatter.format(tool_failure)
    assert formatted == "search: ERROR - timeout"


def test_emoji_formatter():
    """Test emoji formatter output."""
    formatter = EmojiFormatter()

    # Direct event notification
    reason_notification = Notification("reason", {"state": "thinking"})
    formatted = formatter.format(reason_notification)
    assert formatted == "💭 Reason thinking"

    # Tool execution with emoji
    tool_notification = Notification("tool", {"name": "search", "ok": True, "result": "data"})
    formatted = formatter.format(tool_notification)
    assert formatted == "🔍 search: ✅ data"

    # Memory save
    memory_notification = Notification(
        "memory", {"content": "User likes Python", "tags": ["preference"]}
    )
    formatted = formatter.format(memory_notification)
    assert "🧠 Memory: ✅ User likes Python" in formatted


def test_json_formatter():
    """Test JSON formatter output."""
    formatter = JSONFormatter()

    notification = Notification("reason", {"state": "thinking"})
    formatted = formatter.format(notification)

    import json

    data = json.loads(formatted)
    assert data["type"] == "reason"
    assert data["state"] == "thinking"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_core_emit_function():
    """Test core emit function with callbacks."""
    callback = AsyncMock()
    notification = Notification("test", {"message": "hello"})

    await emit(notification, callback)

    callback.assert_called_once_with(notification)


def test_setup_formatter_factory():
    """Test setup_formatter factory function."""
    cli_formatter = setup_formatter(notify=True, debug=False, style="cli")
    assert isinstance(cli_formatter, CLIFormatter)

    emoji_formatter = setup_formatter(notify=True, debug=False, style="emoji")
    assert isinstance(emoji_formatter, EmojiFormatter)

    json_formatter = setup_formatter(notify=True, debug=False, style="json")
    assert isinstance(json_formatter, JSONFormatter)

    silent_formatter = setup_formatter(notify=False, debug=False, style="silent")
    assert isinstance(silent_formatter, Formatter)

    # Default case
    default_formatter = setup_formatter(style="unknown")
    assert isinstance(default_formatter, EmojiFormatter)


def test_formatter_result_truncation():
    """Test result formatting handles long results."""
    formatter = CLIFormatter()

    long_result = "x" * 150  # Longer than 100 char limit
    notification = Notification("tool", {"name": "test", "ok": True, "result": long_result})

    formatted = formatter.format(notification)
    assert len(formatted) < len(f"test: {long_result}")
    assert "..." in formatted


def test_unknown_notification_type():
    """Test formatters handle unknown notification types gracefully."""
    formatter = EmojiFormatter()

    unknown_notification = Notification("unknown_type", {"data": "test"})
    formatted = formatter.format(unknown_notification)
    assert "Unknown notification" in formatted


def test_empty_notification_data():
    """Test formatters handle empty data gracefully."""
    formatter = EmojiFormatter()

    empty_notification = Notification("reason", {})
    formatted = formatter.format(empty_notification)
    # Should not raise exception, should return some string
    assert isinstance(formatted, str)
    assert len(formatted) > 0
