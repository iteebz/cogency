"""Clean tests for telemetry exporters."""

import json

import pytest

from cogency.observe.exporters import OpenTelemetry, Prometheus
from cogency.observe.handlers import MetricsHandler


@pytest.fixture
def metrics():
    m = MetricsHandler()
    # Simulate events to populate metrics
    m.handle({"type": "requests", "data": {}, "timestamp": 123})
    m.handle({"type": "start", "data": {"query": "test"}, "timestamp": 100})
    m.handle(
        {
            "type": "tool",
            "data": {"name": "search", "ok": True, "duration": 0.123},
            "timestamp": 101,
        }
    )
    m.handle(
        {
            "type": "tool",
            "data": {"name": "search", "ok": True, "duration": 0.456},
            "timestamp": 102,
        }
    )
    m.handle({"type": "respond", "data": {"state": "complete"}, "timestamp": 105})
    return m


def test_prometheus_export(metrics):
    exporter = Prometheus(metrics)
    output = exporter.export()

    assert "cogency_events_total" in output
    assert 'type="requests"' in output
    assert 'type="start"' in output
    assert "cogency_tool_duration_seconds_count" in output
    assert "cogency_tool_duration_seconds_sum" in output
    assert "cogency_sessions_total" in output


def test_prometheus_empty():
    empty_metrics = MetricsHandler()
    exporter = Prometheus(empty_metrics)
    output = exporter.export()

    assert output == ""


def test_opentelemetry_export(metrics):
    exporter = OpenTelemetry(metrics, service_name="test-service")
    data = exporter.export()

    assert "resourceMetrics" in data
    resource = data["resourceMetrics"][0]["resource"]
    assert any(attr["key"] == "service.name" for attr in resource["attributes"])

    scope_metrics = data["resourceMetrics"][0]["scopeMetrics"][0]["metrics"]
    metric_names = [m["name"] for m in scope_metrics]

    assert "cogency.requests" in metric_names
    assert "cogency.start" in metric_names
    assert "cogency.tool_duration" in metric_names


def test_json_export(metrics):
    exporter = OpenTelemetry(metrics)
    json_output = exporter.export_json()

    # Should be valid JSON
    parsed = json.loads(json_output)
    assert "resourceMetrics" in parsed


def test_label_formatting():
    metrics = MetricsHandler()
    metrics.handle({"type": "test", "data": {"key1": "val1", "key2": "val2"}, "timestamp": 123})

    exporter = Prometheus(metrics)
    output = exporter.export()

    # Should contain test event count in new format
    assert "cogency_events_total" in output
    assert 'type="test"' in output


def test_opentelemetry_attributes():
    metrics = MetricsHandler()
    metrics.handle({"type": "test", "data": {"env": "prod", "region": "us-east"}, "timestamp": 123})

    exporter = OpenTelemetry(metrics)
    data = exporter.export()

    test_metric = next(
        m
        for m in data["resourceMetrics"][0]["scopeMetrics"][0]["metrics"]
        if m["name"] == "cogency.test"
    )

    # Should be a sum metric (counter) with the event count
    assert "sum" in test_metric
    assert test_metric["sum"]["dataPoints"][0]["asInt"] == 1
