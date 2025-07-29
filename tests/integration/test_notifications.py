"""Simple integration tests for notification system functionality."""

from unittest.mock import AsyncMock

import pytest

from cogency.phases.preprocess import preprocess
from cogency.phases.respond import respond
from cogency.state import State
from cogency.utils.notify import NotificationFormatter, Notifier


@pytest.mark.asyncio
async def test_phase_notifications_direct():
    """Test notifications work directly with phase functions."""
    notifier = Notifier(verbose=True, trace=True)

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

    # Check for respond phase notifications
    respond_notifications = [n for n in notifier.notifications if n.phase == "respond"]
    assert len(respond_notifications) >= 1
    assert "response" in respond_notifications[0].message.lower()


def test_notification_formatter_integration():
    """Test notification formatter with real notifications."""
    notifier = Notifier(verbose=True)

    # Generate some notifications
    notifier.preprocess("Analyzing query structure")
    notifier.reason("Considering available options")
    notifier.action("Executing search tool")
    notifier.respond("Generating final response")

    # Test formatting
    formatter = NotificationFormatter()

    formatted_messages = []
    for notification in notifier.notifications:
        formatted = formatter.format(notification, include_emoji=True)
        formatted_messages.append(formatted)

    # Verify emoji formatting
    assert "⚙️ Analyzing query structure" in formatted_messages
    assert "💭 Considering available options" in formatted_messages
    assert "⚡ Executing search tool" in formatted_messages
    assert "🤖 Generating final response" in formatted_messages


@pytest.mark.asyncio
async def test_callback_integration():
    """Test callback mechanism works with phase notifications."""
    callback_messages = []

    async def test_callback(phase, message, metadata):
        callback_messages.append((phase, message, metadata))

    notifier = Notifier(callback=test_callback, verbose=True)

    # Send notifications
    notifier.preprocess("Starting preprocessing")
    notifier.reason("Analyzing query", {"mode": "fast"})
    notifier.action("Tool execution")

    # Allow async callbacks to complete
    import asyncio

    await asyncio.sleep(0.01)

    # Verify callbacks were triggered
    assert len(callback_messages) == 3
    assert callback_messages[0] == ("preprocess", "Starting preprocessing", {})
    assert callback_messages[1] == ("reason", "Analyzing query", {"mode": "fast"})
    assert callback_messages[2] == ("action", "Tool execution", {})


def test_trace_filtering_integration():
    """Test trace filtering works as expected."""
    # Notifier with trace disabled
    notifier_no_trace = Notifier(trace=False, verbose=True)
    notifier_no_trace.reason("Normal message")
    notifier_no_trace.trace("Debug message")

    # Should only have reason notification
    assert len(notifier_no_trace.notifications) == 1
    assert notifier_no_trace.notifications[0].phase == "reason"

    # Notifier with trace enabled
    notifier_with_trace = Notifier(trace=True, verbose=True)
    notifier_with_trace.reason("Normal message")
    notifier_with_trace.trace("Debug message")

    # Should have both notifications
    assert len(notifier_with_trace.notifications) == 2
    phases = [n.phase for n in notifier_with_trace.notifications]
    assert "reason" in phases
    assert "trace" in phases
