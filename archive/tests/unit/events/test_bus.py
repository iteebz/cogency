"""Unit tests for core event emission infrastructure."""

from unittest.mock import MagicMock

from cogency.events.bus import MessageBus, emit, init_bus


def test_subscribe():
    bus = MessageBus()
    handler = MagicMock()

    bus.subscribe(handler)

    assert handler in bus.handlers


def test_emit_calls_handlers():
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


def test_emit_empty():
    bus = MessageBus()
    handler = MagicMock()
    bus.subscribe(handler)

    bus.emit("simple_event")

    call_event = handler.handle.call_args[0][0]
    assert call_event["type"] == "simple_event"
    assert call_event["data"] == {}


def test_emit_no_bus():
    """Global emit without bus does nothing."""
    # Reset global bus
    init_bus(None)

    # Should not raise error
    emit("test_event", data="value")


def test_emit_forwards_to_bus():
    """Global emit forwards to initialized bus."""
    bus = MessageBus()
    handler = MagicMock()
    bus.subscribe(handler)
    init_bus(bus)

    emit("global_event", key="value")

    handler.handle.assert_called_once()
    call_event = handler.handle.call_args[0][0]
    assert call_event["type"] == "global_event"
    assert call_event["data"] == {"key": "value"}


def test_init_bus():
    """Bus initialization enables global emit."""
    bus = MessageBus()
    handler = MagicMock()
    bus.subscribe(handler)

    init_bus(bus)
    emit("test")

    handler.handle.assert_called_once()
