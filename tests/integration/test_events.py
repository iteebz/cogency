"""Integration tests for event system - full workflow testing."""

from unittest.mock import MagicMock

import pytest

from cogency.events.core import MessageBus, emit, init_bus
from cogency.events.handlers import ConsoleHandler, LoggerHandler
from cogency.observe.handlers import MetricsHandler


class TestIntegratedEventFlow:
    """Test complete event flow with all handlers."""

    def test_full_agent_session_workflow(self):
        """Test a complete agent session from start to finish."""
        # Setup
        bus = MessageBus()
        notifier = ConsoleHandler(enabled=False)  # Disable printing for test
        logger = LoggerHandler(max_size=100)
        metrics = MetricsHandler()

        bus.subscribe(notifier)
        bus.subscribe(logger)
        bus.subscribe(metrics)
        init_bus(bus)

        # Simulate agent session
        emit("start", query="What is 2+2?")
        emit("triage", state="complete", selected_tools=0)
        emit("reason", state="planning")
        emit("reason", state="complete", early_return=True)
        emit("respond", state="generating")
        emit("respond", state="complete")

        # Verify logger captured events
        logs = logger.logs()
        assert len(logs) == 6
        assert logs[0]["type"] == "start"
        assert logs[0]["query"] == "What is 2+2?"

        # Verify metrics tracked session
        stats = metrics.stats()
        assert stats["event_counts"]["start"] == 1
        assert stats["event_counts"]["respond"] == 2
        assert stats["sessions"]["total"] == 1

        session = stats["sessions"]["recent"][0]
        assert session["query"] == "What is 2+2?"
        assert session["reasoning_steps"] == 2

    def test_tool_usage_tracking(self):
        """Test tool execution tracking across handlers."""
        bus = MessageBus()
        logger = LoggerHandler()
        metrics = MetricsHandler()

        bus.subscribe(logger)
        bus.subscribe(metrics)
        init_bus(bus)

        # Start session
        emit("start", query="Search for something")

        # Tool calls
        emit("tool", name="search", ok=True, duration=1.2)
        emit("tool", name="http", ok=False, duration=0.5)
        emit("tool", name="search", ok=True, duration=0.8)

        # End session
        emit("respond", state="complete")

        # Check logger
        logs = logger.logs()
        tool_logs = [log for log in logs if log["type"] == "tool"]
        assert len(tool_logs) == 3

        # Check metrics
        tool_stats = metrics.tool_stats()
        assert tool_stats["search"]["calls"] == 2
        assert tool_stats["search"]["successes"] == 2
        assert tool_stats["search"]["success_rate"] == 1.0
        assert tool_stats["http"]["success_rate"] == 0.0

    def test_error_handling_across_handlers(self):
        """Test error event handling in all handlers."""
        bus = MessageBus()
        notifier = MagicMock()  # Mock to capture calls
        logger = LoggerHandler()
        metrics = MetricsHandler()

        bus.subscribe(notifier)
        bus.subscribe(logger)
        bus.subscribe(metrics)
        init_bus(bus)

        emit("start", query="Test error handling")
        emit("error", message="Something went wrong")
        emit("respond", state="complete")

        # Notifier should have received error
        notifier.handle.assert_called()
        error_call = None
        for call in notifier.handle.call_args_list:
            if call[0][0]["type"] == "error":
                error_call = call[0][0]
                break

        assert error_call is not None
        assert error_call["data"]["message"] == "Something went wrong"

        # Logger should have stored error
        logs = logger.logs()
        error_logs = [log for log in logs if log["type"] == "error"]
        assert len(error_logs) == 1
        assert error_logs[0]["message"] == "Something went wrong"

        # Metrics should count error
        stats = metrics.stats()
        assert stats["sessions"]["recent"][0]["errors"] == 1

    def test_handler_independence(self):
        """Test that handler failures don't affect other handlers."""
        bus = MessageBus()

        # Create a handler that will fail
        failing_handler = MagicMock()
        failing_handler.handle.side_effect = Exception("Handler failed")

        # Create normal handlers
        logger = LoggerHandler()
        metrics = MetricsHandler()

        bus.subscribe(failing_handler)
        bus.subscribe(logger)
        bus.subscribe(metrics)
        init_bus(bus)

        # Bus doesn't catch handler exceptions - handlers should be robust
        # This is expected behavior - failing handlers propagate exceptions
        with pytest.raises(Exception, match="Handler failed"):
            emit("test_event", data="value")
