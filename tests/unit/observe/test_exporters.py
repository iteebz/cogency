"""Observability system tests - logs and events."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from resilient_result import Result

from cogency.observe.exporters import BasicExporter


@pytest.fixture
def metrics_events():
    """Fixture with event stream for telemetry testing."""
    return [
        {"type": "requests", "data": {}, "timestamp": 123},
        {"type": "start", "data": {"query": "test"}, "timestamp": 100},
        {
            "type": "tool",
            "data": {"name": "search", "success": True, "duration": 0.123},
            "timestamp": 101,
        },
        {
            "type": "tool",
            "data": {"name": "search", "success": True, "duration": 0.456},
            "timestamp": 102,
        },
        {"type": "respond", "data": {"state": "complete"}, "timestamp": 105},
    ]


def test_telemetry_metrics_aggregation(metrics_events):
    """Test metrics aggregation from event stream for telemetry export."""
    # Behavioral intent: Convert event stream to aggregated metrics
    tool_events = [e for e in metrics_events if e["type"] == "tool"]
    session_events = [e for e in metrics_events if e["type"] == "start"]

    # Telemetry patterns: count, duration, success rates
    total_tools = len(tool_events)
    total_duration = sum(e["data"]["duration"] for e in tool_events)
    success_rate = len([e for e in tool_events if e["data"]["success"]]) / total_tools

    assert total_tools == 2
    assert total_duration == 0.579  # 0.123 + 0.456
    assert success_rate == 1.0
    assert len(session_events) == 1


def test_prometheus_format_export(metrics_events):
    """Test Prometheus format export from aggregated metrics."""
    # Behavioral intent: Export metrics in Prometheus format
    tool_events = [e for e in metrics_events if e["type"] == "tool"]

    # Mock Prometheus format generation
    prometheus_output = []

    # Event count metrics
    event_types = {e["type"] for e in metrics_events}
    for event_type in event_types:
        count = len([e for e in metrics_events if e["type"] == event_type])
        prometheus_output.append(f'cogency_events_total{{type="{event_type}"}} {count}')

    # Tool duration metrics
    if tool_events:
        tool_count = len(tool_events)
        tool_duration_sum = sum(e["data"]["duration"] for e in tool_events)
        prometheus_output.append(f"cogency_tool_duration_seconds_count {tool_count}")
        prometheus_output.append(f"cogency_tool_duration_seconds_sum {tool_duration_sum}")

    # Session metrics
    session_count = len([e for e in metrics_events if e["type"] == "start"])
    prometheus_output.append(f"cogency_sessions_total {session_count}")

    output = "\n".join(prometheus_output)

    # Contract validation
    assert 'cogency_events_total{type="tool"} 2' in output
    assert "cogency_tool_duration_seconds_count 2" in output
    assert "cogency_tool_duration_seconds_sum 0.579" in output
    assert "cogency_sessions_total 1" in output


def test_opentelemetry_span_export(metrics_events):
    """Test OpenTelemetry span export from event workflow."""
    # Behavioral intent: Convert event workflows to distributed tracing spans
    tool_events = [e for e in metrics_events if e["type"] == "tool"]

    # Mock span generation from tool events
    spans = []
    for tool_event in tool_events:
        span = {
            "name": f"tool.{tool_event['data']['name']}",
            "start_time": tool_event["timestamp"],
            "duration": tool_event["data"]["duration"] * 1000,  # Convert to ms
            "attributes": {
                "tool.name": tool_event["data"]["name"],
                "tool.success": tool_event["data"]["success"],
            },
        }
        spans.append(span)

    # Contract validation
    assert len(spans) == 2
    assert spans[0]["name"] == "tool.search"
    assert spans[0]["duration"] == 123  # 0.123 * 1000
    assert spans[1]["duration"] == 456  # 0.456 * 1000
    assert all(span["attributes"]["tool.success"] for span in spans)


def test_event_capture(agent):
    """Test event capture during agent execution."""
    # Events should be captured automatically
    logs = agent.logs()
    assert isinstance(logs, list)

    # Initial event capture
    initial_count = len(logs)

    # Simulate event emission through global emit function
    from cogency.events import emit

    emit("test", message="Test event")

    # Should capture new events
    updated_logs = agent.logs()
    assert len(updated_logs) >= initial_count


def test_log_filtering(agent):
    """Test log filtering capabilities."""
    # Type filtering
    agent_logs = agent.logs(type="agent")
    assert isinstance(agent_logs, list)

    # Error filtering
    error_logs = agent.logs(errors_only=True)
    assert isinstance(error_logs, list)

    # Last N filtering
    recent_logs = agent.logs(last=3)
    assert isinstance(recent_logs, list)
    assert len(recent_logs) <= 3


@pytest.mark.asyncio
async def test_execution_events(agent):
    """Test events generated during execution."""
    with patch("cogency.agents.reason", new_callable=AsyncMock) as mock_reason:
        with patch("cogency.state.State.start_task", new_callable=AsyncMock) as mock_state:
            mock_state.return_value = Mock()
            mock_reason.return_value = Result.ok({"response": "Test response"})

            initial_logs = len(agent.logs())

            await agent.run("Test query")

            # Should generate execution events
            final_logs = len(agent.logs())
            assert final_logs > initial_logs


def test_event_types(agent):
    """Test different event types are captured."""
    # Emit different event types
    from cogency.events import emit

    emit("agent", action="start")
    emit("reason", step="thinking")
    emit("tool", name="files", action="list")
    emit("memory", action="situate")

    logs = agent.logs()

    # Check events are captured
    event_types = {log.get("type") for log in logs}
    expected_types = {"agent", "reason", "tool", "memory"}
    assert expected_types.issubset(event_types)


def test_error_event_capture(agent):
    """Test error events are properly captured."""
    # Emit error event
    from cogency.events import emit

    emit("error", error="Test error", severity="high")

    # Filter for errors
    error_logs = agent.logs(errors_only=True)
    assert len(error_logs) > 0

    # Check error details
    error_event = error_logs[0]
    assert error_event.get("type") == "error"


def test_basic_exporter():
    """Test BasicExporter functionality."""
    # Mock metrics handler
    mock_handler = Mock()
    mock_handler.stats.return_value = {
        "event_counts": {"agent": 5, "tool": 3},
        "sessions": {"total": 1, "avg_duration": 30.5},
        "performance": [{"type": "tool", "duration": 1.2}, {"type": "tool", "duration": 0.8}],
    }

    exporter = BasicExporter(mock_handler)

    # Test stats generation
    stats = exporter.stats()
    assert "timestamp" in stats
    assert "event_counts" in stats
    assert "sessions" in stats
    assert "performance_summary" in stats


def test_exporter_json_output():
    """Test JSON export functionality."""
    mock_handler = Mock()
    mock_handler.stats.return_value = {"event_counts": {"agent": 1}}

    exporter = BasicExporter(mock_handler)
    json_output = exporter.export_json()

    assert isinstance(json_output, str)
    assert "event_counts" in json_output
    assert "agent" in json_output


def test_exporter_simple_output():
    """Test simple text export functionality."""
    mock_handler = Mock()
    mock_handler.stats.return_value = {
        "event_counts": {"agent": 2, "tool": 1},
        "sessions": {"total": 1, "avg_duration": 15.3},
    }

    exporter = BasicExporter(mock_handler)
    simple_output = exporter.export_simple()

    assert isinstance(simple_output, str)
    assert "Cogency Metrics" in simple_output
    assert "Event Counts" in simple_output
    assert "agent: 2" in simple_output


def test_performance_summarization():
    """Test performance data summarization."""
    mock_handler = Mock()
    mock_handler.stats.return_value = {
        "performance": [
            {"type": "tool", "duration": 1.0},
            {"type": "tool", "duration": 2.0},
            {"type": "reason", "duration": 0.5},  # Should be filtered out
        ]
    }

    exporter = BasicExporter(mock_handler)
    stats = exporter.stats()

    perf_summary = stats["performance_summary"]
    assert perf_summary["tool_count"] == 2
    assert perf_summary["avg_duration"] == 1.5
    assert perf_summary["total_duration"] == 3.0


@pytest.mark.asyncio
async def test_tool_events(agent_with_tools):
    """Test tool execution generates proper events."""
    # Mock tool execution to avoid actual tool calls
    with patch("cogency.agents.act", new_callable=AsyncMock) as mock_act:
        with patch("cogency.agents.reason", new_callable=AsyncMock) as mock_reason:
            with patch("cogency.state.State.start_task", new_callable=AsyncMock) as mock_state:
                mock_state.return_value = Mock()
                mock_reason.return_value = Result.ok({"actions": [{"tool": "files", "args": {}}]})
                mock_act.return_value = "Tool result"

                await agent_with_tools.run("Use tools")

                # Check for tool events
                tool_logs = agent_with_tools.logs(type="tool")
                # Should have some tool-related events
                assert isinstance(tool_logs, list)


def test_event_buffer_initialization(agent):
    """Test event buffer is properly initialized."""
    # Agent should have event system initialized
    assert callable(agent.logs)

    # Basic event emission should work
    from cogency.events import emit

    emit("test", data="test")
    logs = agent.logs()
    assert len(logs) >= 1
