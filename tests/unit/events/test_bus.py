"""Unit tests for core event emission infrastructure."""

from unittest.mock import MagicMock

from cogency.events.bus import MessageBus, emit, init_bus


class TestMessageBus:
    """Test MessageBus emission and subscription."""

    def test_subscribe_adds_handler(self):
        bus = MessageBus()
        handler = MagicMock()

        bus.subscribe(handler)

        assert handler in bus.handlers

    def test_emit_calls_all_handlers(self):
        bus = MessageBus()
        handler1 = MagicMock()
        handler2 = MagicMock()
        bus.subscribe(handler1)
        bus.subscribe(handler2)

        bus.emit("test_event", key="value")

        handler1.handle.assert_called_once()
        handler2.handle.assert_called_once()

        # Check event structure
        call_event = handler1.handle.call_args[0][0]
        assert call_event["type"] == "test_event"
        assert call_event["data"] == {"key": "value"}
        assert "timestamp" in call_event

    def test_emit_empty_payload(self):
        bus = MessageBus()
        handler = MagicMock()
        bus.subscribe(handler)

        bus.emit("simple_event")

        call_event = handler.handle.call_args[0][0]
        assert call_event["type"] == "simple_event"
        assert call_event["data"] == {}


class TestGlobalEmit:
    """Test global emit function and bus initialization."""

    def test_emit_no_bus_does_nothing(self):
        # Reset global bus
        init_bus(None)

        # Should not raise error
        emit("test_event", data="value")

    def test_emit_with_bus_forwards_to_bus(self):
        bus = MessageBus()
        handler = MagicMock()
        bus.subscribe(handler)
        init_bus(bus)

        emit("global_event", key="value")

        handler.handle.assert_called_once()
        call_event = handler.handle.call_args[0][0]
        assert call_event["type"] == "global_event"
        assert call_event["data"] == {"key": "value"}

    def test_init_bus_sets_global(self):
        bus = MessageBus()
        handler = MagicMock()
        bus.subscribe(handler)

        init_bus(bus)
        emit("test")

        handler.handle.assert_called_once()
