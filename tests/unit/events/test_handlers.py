"""Unit tests for event handlers."""

from collections import deque
from io import StringIO
from unittest.mock import patch

import pytest

from cogency.events.handlers import ConsoleHandler, LoggerHandler
from cogency.observe.handlers import MetricsHandler


class TestConsoleHandler:
    """Test ConsoleHandler outputs and behavior."""

    def test_disabled_handler_outputs_nothing(self):
        handler = ConsoleHandler(enabled=False)

        with patch("builtins.print") as mock_print:
            handler.handle({"type": "start", "data": {"query": "test"}, "timestamp": 123})
            mock_print.assert_not_called()

    def test_start_event_with_query(self):
        handler = ConsoleHandler(enabled=True)

        with patch("builtins.print") as mock_print:
            handler.handle({"type": "start", "data": {"query": "Hello world"}, "timestamp": 123})

            assert mock_print.call_count == 2
            mock_print.assert_any_call("🚀 Starting agent...")
            mock_print.assert_any_call("📝 Hello world")

    def test_agent_create_complete(self):
        handler = ConsoleHandler(enabled=True)

        with patch("builtins.print") as mock_print:
            handler.handle(
                {
                    "type": "agent_create",
                    "data": {"name": "test_agent", "status": "complete"},
                    "timestamp": 123,
                }
            )
            mock_print.assert_called_once_with("✅ Agent 'test_agent' ready")

    def test_tool_success_with_duration(self):
        handler = ConsoleHandler(enabled=True)

        with patch("builtins.print") as mock_print:
            handler.handle(
                {
                    "type": "tool",
                    "data": {"name": "search", "ok": True, "duration": 1.5},
                    "timestamp": 123,
                }
            )
            mock_print.assert_called_once_with("✅ search (1.5s)")

    def test_error_event(self):
        handler = ConsoleHandler(enabled=True)

        with patch("builtins.print") as mock_print:
            handler.handle(
                {"type": "error", "data": {"message": "Something went wrong"}, "timestamp": 123}
            )
            mock_print.assert_called_once_with("❌ Something went wrong")

    def test_debug_event_only_when_debug_enabled(self):
        handler_debug = ConsoleHandler(enabled=True, debug=True)
        handler_no_debug = ConsoleHandler(enabled=True, debug=False)

        event = {"type": "debug", "data": {"message": "Debug info"}, "timestamp": 123}

        with patch("builtins.print") as mock_print:
            handler_debug.handle(event)
            mock_print.assert_called_once_with("🐛 Debug info")

            mock_print.reset_mock()
            handler_no_debug.handle(event)
            mock_print.assert_not_called()


class TestLoggerHandler:
    """Test LoggerHandler event storage and filtering."""

    def test_stores_events_in_structured_format(self):
        handler = LoggerHandler(max_size=10, structured=True)

        handler.handle({"type": "start", "data": {"query": "test"}, "timestamp": 123.45})

        logs = handler.logs()
        assert len(logs) == 1
        assert logs[0] == {"timestamp": 123.45, "type": "start", "query": "test"}

    def test_stores_raw_events_when_structured_false(self):
        handler = LoggerHandler(max_size=10, structured=False)

        event = {"type": "start", "data": {"query": "test"}, "timestamp": 123.45}
        handler.handle(event)

        logs = handler.logs()
        assert len(logs) == 1
        assert logs[0] == event

    def test_filters_config_load_noise(self):
        handler = LoggerHandler(max_size=10, structured=True)
        handler.config["filter_noise"] = True

        # Should be filtered
        handler.handle({"type": "config_load", "data": {"status": "loading"}, "timestamp": 123})
        handler.handle({"type": "config_load", "data": {"status": "complete"}, "timestamp": 124})

        # Should not be filtered
        handler.handle({"type": "config_load", "data": {"status": "error"}, "timestamp": 125})
        handler.handle({"type": "start", "data": {"query": "test"}, "timestamp": 126})

        logs = handler.logs()
        assert len(logs) == 2
        assert logs[0]["type"] == "config_load"
        assert logs[0]["status"] == "error"
        assert logs[1]["type"] == "start"

    def test_max_size_rolling_buffer(self):
        handler = LoggerHandler(max_size=2, structured=True)

        handler.handle({"type": "event1", "data": {}, "timestamp": 1})
        handler.handle({"type": "event2", "data": {}, "timestamp": 2})
        handler.handle({"type": "event3", "data": {}, "timestamp": 3})

        logs = handler.logs()
        assert len(logs) == 2
        assert logs[0]["type"] == "event2"
        assert logs[1]["type"] == "event3"

    def test_configuration_update(self):
        handler = LoggerHandler()

        handler.configure(filter_noise=False, max_size=500)

        assert handler.config["filter_noise"] is False
        assert handler.config["max_size"] == 500


class TestMetricsHandler:
    """Test MetricsHandler stats collection."""

    def test_counts_all_event_types(self):
        handler = MetricsHandler()

        handler.handle({"type": "start", "data": {}, "timestamp": 123})
        handler.handle({"type": "start", "data": {}, "timestamp": 124})
        handler.handle({"type": "tool", "data": {}, "timestamp": 125})

        stats = handler.stats()
        assert stats["event_counts"]["start"] == 2
        assert stats["event_counts"]["tool"] == 1

    def test_session_tracking(self):
        handler = MetricsHandler()

        # Start session
        handler.handle({"type": "start", "data": {"query": "test query"}, "timestamp": 100})

        # Session events
        handler.handle(
            {
                "type": "tool",
                "data": {"name": "search", "ok": True, "duration": 1.0},
                "timestamp": 101,
            }
        )
        handler.handle({"type": "reason", "data": {}, "timestamp": 102})
        handler.handle({"type": "error", "data": {}, "timestamp": 103})

        # Complete session
        handler.handle({"type": "respond", "data": {"state": "complete"}, "timestamp": 105})

        stats = handler.stats()
        sessions = stats["sessions"]

        assert sessions["total"] == 1
        assert len(sessions["recent"]) == 1

        session = sessions["recent"][0]
        assert session["query"] == "test query"
        assert session["tools_used"] == 1
        assert session["reasoning_steps"] == 1
        assert session["errors"] == 1
        assert session["duration"] == 5  # 105 - 100

    def test_tool_performance_tracking(self):
        handler = MetricsHandler()

        # Start session first (required for tool tracking)
        handler.handle({"type": "start", "data": {"query": "test"}, "timestamp": 99})

        handler.handle(
            {
                "type": "tool",
                "data": {"name": "search", "ok": True, "duration": 1.5},
                "timestamp": 100,
            }
        )
        handler.handle(
            {
                "type": "tool",
                "data": {"name": "search", "ok": False, "duration": 0.5},
                "timestamp": 101,
            }
        )
        handler.handle(
            {
                "type": "tool",
                "data": {"name": "http", "ok": True, "duration": 2.0},
                "timestamp": 102,
            }
        )

        tool_stats = handler.tool_stats()

        search_stats = tool_stats["search"]
        assert search_stats["calls"] == 2
        assert search_stats["successes"] == 1
        assert search_stats["success_rate"] == 0.5
        assert search_stats["total_duration"] == 2.0
        assert search_stats["avg_duration"] == 1.0

        http_stats = tool_stats["http"]
        assert http_stats["calls"] == 1
        assert http_stats["success_rate"] == 1.0

    def test_concurrent_sessions_isolation(self):
        handler = MetricsHandler()

        # Start first session
        handler.handle({"type": "start", "data": {"query": "first"}, "timestamp": 100})
        handler.handle({"type": "tool", "data": {"name": "search"}, "timestamp": 101})

        # Complete first session
        handler.handle({"type": "respond", "data": {"state": "complete"}, "timestamp": 105})

        # Start second session
        handler.handle({"type": "start", "data": {"query": "second"}, "timestamp": 110})
        handler.handle({"type": "tool", "data": {"name": "http"}, "timestamp": 111})

        # Check current session tracking
        stats = handler.stats()
        assert stats["sessions"]["current"]["query"] == "second"
        assert stats["sessions"]["current"]["tools_used"] == 1
        assert stats["sessions"]["total"] == 1  # Only completed sessions
