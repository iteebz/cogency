"""Telemetry bridge unit tests - CLI event surfacing validation."""

import time
from unittest.mock import Mock

from cogency.events.bus import MessageBus
from cogency.events.handlers import EventBuffer
from cogency.events.telemetry import TelemetryBridge, create_telemetry_bridge, format_telemetry_summary


def test_telemetry_bridge_creation():
    """Test telemetry bridge initialization."""
    bus = MessageBus()
    bridge = TelemetryBridge(bus)
    
    assert bridge.bus is bus
    assert isinstance(bridge.buffer, EventBuffer)
    assert bridge.buffer in bus.handlers


def test_telemetry_bridge_factory():
    """Test canonical bridge creation function."""
    bus = MessageBus()
    bridge = create_telemetry_bridge(bus)
    
    assert isinstance(bridge, TelemetryBridge)
    assert bridge.bus is bus


def test_event_collection():
    """Test event collection and filtering."""
    bus = MessageBus()
    bridge = TelemetryBridge(bus)
    
    # Emit test events
    bus.emit("tool", name="files", operation="list", status="start")
    bus.emit("tool", name="files", operation="list", status="complete")
    bus.emit("agent", state="iteration", iteration=0)
    bus.emit("log", level="error", message="Test error")
    
    # Test recent events retrieval
    recent = bridge.get_recent(count=10)
    assert len(recent) == 4
    
    # Test filtering by type
    tool_events = bridge.get_recent(count=10, filters={"type": "tool"})
    assert len(tool_events) == 2
    assert all(e["type"] == "tool" for e in tool_events)
    
    # Test error filtering
    error_events = bridge.get_recent(count=10, filters={"errors_only": True})
    assert len(error_events) == 1
    assert error_events[0]["level"] == "error"


def test_event_formatting():
    """Test event formatting for CLI display."""
    bus = MessageBus()
    bridge = TelemetryBridge(bus)
    
    # Create test event
    test_event = {
        "type": "tool",
        "level": "info", 
        "timestamp": time.time(),
        "data": {
            "name": "files",
            "operation": "list",
            "status": "complete"
        }
    }
    
    # Test compact formatting
    compact = bridge.format_event(test_event, style="compact")
    assert "files" in compact
    assert "complete" in compact
    assert "[tool]" in compact
    
    # Test detailed formatting
    detailed = bridge.format_event(test_event, style="detailed")
    assert "TOOL" in detailed
    assert "files" in detailed
    assert "complete" in detailed


def test_summary_generation():
    """Test telemetry summary generation."""
    bus = MessageBus()
    bridge = TelemetryBridge(bus)
    
    # Emit various events
    start_time = time.time()
    bus.emit("agent", state="start")
    bus.emit("tool", name="files", status="start")
    bus.emit("tool", name="files", status="complete")
    bus.emit("tool", name="search", status="start")  
    bus.emit("tool", name="search", status="complete")
    bus.emit("agent", state="iteration", iteration=0)
    bus.emit("agent", state="iteration", iteration=1)
    bus.emit("log", level="error", message="Test error")
    bus.emit("agent", state="complete")
    
    summary = bridge.get_summary()
    
    # Verify summary structure
    assert "total_events" in summary
    assert "event_types" in summary
    assert "tools_used" in summary
    assert "iterations" in summary
    assert "errors" in summary
    assert "duration" in summary
    
    # Verify metrics
    assert summary["total_events"] == 9
    assert summary["iterations"] == 2  # Two iteration events
    assert summary["errors"] == 1  # One error event
    assert "files" in summary["tools_used"]
    assert "search" in summary["tools_used"]
    
    # Verify event type counts
    event_types = summary["event_types"]
    assert event_types["agent"] == 4  # start, 2 iterations, complete
    assert event_types["tool"] == 4   # 2 tools x 2 events each
    assert event_types["log"] == 1    # 1 error


def test_emoji_selection():
    """Test appropriate emoji selection for different event types."""
    bridge = TelemetryBridge()
    
    # Test event type emojis
    assert bridge._get_event_emoji("tool", "info", {}) == "🔧"
    assert bridge._get_event_emoji("agent", "info", {}) == "🧠"
    assert bridge._get_event_emoji("memory", "info", {}) == "💾"
    assert bridge._get_event_emoji("security", "info", {}) == "🔒"
    
    # Test error level override
    assert bridge._get_event_emoji("tool", "error", {}) == "❌"
    assert bridge._get_event_emoji("agent", "error", {}) == "❌"
    
    # Test status-based overrides
    assert bridge._get_event_emoji("tool", "info", {"status": "complete"}) == "✅"
    assert bridge._get_event_emoji("tool", "info", {"status": "error"}) == "❌"
    assert bridge._get_event_emoji("agent", "info", {"state": "complete"}) == "🎯"


def test_content_extraction():
    """Test meaningful content extraction from events."""
    bridge = TelemetryBridge()
    
    # Tool event content
    tool_content = bridge._get_event_content("tool", {
        "name": "files", 
        "operation": "list",
        "status": "complete"
    })
    assert tool_content == "files.list → complete"
    
    # Agent event content
    agent_content = bridge._get_event_content("agent", {
        "state": "iteration",
        "iteration": 2
    })
    assert agent_content == "iteration 2"
    
    # Memory event content
    memory_content = bridge._get_event_content("memory", {
        "operation": "save"
    })
    assert memory_content == "memory.save"


def test_filter_application():
    """Test event filtering logic."""
    bridge = TelemetryBridge()
    
    events = [
        {"type": "tool", "level": "info", "data": {"name": "files"}},
        {"type": "agent", "level": "info", "data": {"state": "start"}},
        {"type": "tool", "level": "error", "data": {"name": "search"}},
        {"type": "log", "level": "error", "data": {"message": "Failed"}},
    ]
    
    # Test type filtering
    tool_events = bridge._apply_filters(events, {"type": "tool"})
    assert len(tool_events) == 2
    assert all(e["type"] == "tool" for e in tool_events)
    
    # Test level filtering
    error_events = bridge._apply_filters(events, {"level": "error"})
    assert len(error_events) == 2
    assert all(e["level"] == "error" for e in error_events)
    
    # Test errors_only filtering
    errors_only = bridge._apply_filters(events, {"errors_only": True})
    assert len(errors_only) == 2
    
    # Test tool name filtering  
    files_events = bridge._apply_filters(events, {"tool": "files"})
    assert len(files_events) == 1
    assert files_events[0]["data"]["name"] == "files"


def test_telemetry_summary_formatting():
    """Test summary formatting for CLI display."""
    bus = MessageBus()
    bridge = TelemetryBridge(bus)
    
    # Empty summary
    empty_summary = format_telemetry_summary(bridge)
    assert "No telemetry data" in empty_summary
    
    # Summary with events
    bus.emit("tool", name="files", status="complete")
    bus.emit("agent", state="complete")
    
    summary = format_telemetry_summary(bridge)
    assert "Telemetry Summary" in summary
    assert "Total events: 2" in summary
    assert "tool: 1" in summary
    assert "agent: 1" in summary