"""Clean tests for telemetry exporters."""

import json

import pytest

from cogency.observe.exporters import OpenTelemetry, Prometheus
from cogency.observe.metrics import Metrics


@pytest.fixture
def metrics():
    m = Metrics()
    # Add test data
    m.counter("requests", 42.0, {"service": "api", "status": "200"})
    m.gauge("cpu_usage", 75.5, {"host": "web1"})
    m.histogram("response_time", 0.123, {"endpoint": "/users"})
    m.histogram("response_time", 0.456, {"endpoint": "/users"})
    return m


def test_prometheus_export(metrics):
    exporter = Prometheus(metrics)
    output = exporter.export()

    assert "cogency_requests_total" in output
    assert "cogency_cpu_usage" in output
    assert "cogency_response_time_count" in output
    assert "cogency_response_time_sum" in output
    assert 'service="api"' in output
    assert 'status="200"' in output


def test_prometheus_empty():
    empty_metrics = Metrics()
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
    assert "cogency.cpu_usage" in metric_names
    assert "cogency.response_time" in metric_names


def test_json_export(metrics):
    exporter = OpenTelemetry(metrics)
    json_output = exporter.export_json()

    # Should be valid JSON
    parsed = json.loads(json_output)
    assert "resourceMetrics" in parsed


def test_label_formatting():
    metrics = Metrics()
    metrics.counter("test", 1.0, {"key1": "val1", "key2": "val2"})

    exporter = Prometheus(metrics)
    output = exporter.export()

    # Labels should be sorted and properly formatted
    assert '{key1="val1",key2="val2"}' in output


def test_opentelemetry_attributes():
    metrics = Metrics()
    metrics.gauge("test", 100.0, {"env": "prod", "region": "us-east"})

    exporter = OpenTelemetry(metrics)
    data = exporter.export()

    gauge_metric = next(
        m
        for m in data["resourceMetrics"][0]["scopeMetrics"][0]["metrics"]
        if m["name"] == "cogency.test"
    )
    attributes = gauge_metric["gauge"]["dataPoints"][0]["attributes"]

    assert len(attributes) == 2
    assert {"key": "env", "value": {"stringValue": "prod"}} in attributes
