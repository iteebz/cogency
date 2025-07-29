"""Metrics collection tests - core measurement logic."""

import time
from unittest.mock import mock_open, patch

import pytest

from cogency.observe.metrics import (
    MetricPoint,
    Metrics,
    MetricsReporter,
    MetricsSummary,
    TimerContext,
    counter,
    gauge,
    get_metrics,
    histogram,
    measure,
    timer,
)


@pytest.fixture
def metrics():
    return Metrics(max_points=100)


def test_metric_point():
    point = MetricPoint("test", 1.5, {"tag": "value"})
    assert point.name == "test"
    assert point.value == 1.5
    assert point.tags == {"tag": "value"}
    assert isinstance(point.timestamp, float)


def test_counter(metrics):
    metrics.counter("test", 5.0, {"env": "test"})
    metrics.counter("test", 3.0, {"env": "test"})

    key = "test#env=test"
    assert metrics.counters[key] == 8.0


def test_gauge(metrics):
    metrics.gauge("cpu", 85.5, {"host": "web1"})
    metrics.gauge("cpu", 90.2, {"host": "web1"})  # overwrites

    key = "cpu#host=web1"
    assert metrics.gauges[key] == 90.2


def test_histogram(metrics):
    metrics.histogram("latency", 100.0, {"service": "api"})
    metrics.histogram("latency", 200.0, {"service": "api"})

    key = "latency#service=api"
    assert len(metrics.points[key]) == 2
    assert metrics.points[key][0].value == 100.0
    assert metrics.points[key][1].value == 200.0


def test_timer_context():
    metrics_collector = Metrics()

    with patch("time.time", side_effect=[1.0, 1.5]):
        with metrics_collector.timer("operation", {"type": "test"}):
            pass

    key = "operation#type=test"
    assert len(metrics_collector.points[key]) == 1
    assert metrics_collector.points[key][0].value == 0.5


def test_summary(metrics):
    values = [10, 20, 30, 40, 50]
    for v in values:
        metrics.histogram("test", v)

    summary = metrics.get_summary("test")
    assert summary.name == "test"
    assert summary.count == 5
    assert summary.sum == 150
    assert summary.min == 10
    assert summary.max == 50
    assert summary.avg == 30
    assert summary.p50 == 30


def test_summary_empty(metrics):
    summary = metrics.get_summary("nonexistent")
    assert summary is None


def test_key_generation(metrics):
    key1 = metrics._key("metric", {})
    key2 = metrics._key("metric", {"a": "1", "b": "2"})

    assert key1 == "metric"
    assert key2 == "metric#a=1,b=2"


def test_key_parsing(metrics):
    name, tags = metrics._parse("metric")
    assert name == "metric"
    assert tags == {}

    name, tags = metrics._parse("metric#a=1,b=2")
    assert name == "metric"
    assert tags == {"a": "1", "b": "2"}


def test_reset(metrics):
    metrics.counter("test", 1)
    metrics.gauge("test", 1)
    metrics.histogram("test", 1)

    metrics.reset()

    assert len(metrics.counters) == 0
    assert len(metrics.gauges) == 0
    assert len(metrics.points) == 0


def test_to_dict(metrics):
    metrics.counter("c", 5)
    metrics.gauge("g", 10)
    metrics.histogram("h", 15)

    data = metrics.to_dict()
    assert "counters" in data
    assert "gauges" in data
    assert "histograms" in data


def test_percentile_calculation(metrics):
    values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    p50 = metrics._pct(values, 0.5)
    p95 = metrics._pct(values, 0.95)
    p99 = metrics._pct(values, 0.99)

    assert p50 == 5.5  # median
    assert abs(p95 - 9.55) < 0.01  # Use tolerance for floating point
    assert abs(p99 - 9.91) < 0.01


def test_metrics_reporter(metrics):
    reporter = MetricsReporter(metrics)

    # Add some test data
    metrics.histogram("test", 100.0)
    metrics.histogram("test", 200.0)

    # Test log summary (just ensure no exceptions)
    reporter.log_summary()


def test_to_json(metrics, tmp_path):
    reporter = MetricsReporter(metrics)
    metrics.histogram("test", 100.0)

    filepath = tmp_path / "metrics.json"
    reporter.to_json(str(filepath))

    assert filepath.exists()

    import json

    with open(filepath) as f:
        data = json.load(f)

    assert "timestamp" in data
    assert "summaries" in data
    assert "raw" in data


def test_global_functions():
    # Test module-level convenience functions
    counter("test_counter", 1.0, {"env": "test"})
    gauge("test_gauge", 50.0)
    histogram("test_histogram", 25.0)

    with timer("test_timer"):
        pass

    global_metrics = get_metrics()
    assert len(global_metrics.counters) > 0


def test_measure_decorator():
    @measure("decorated_function")
    def test_func():
        return "result"

    result = test_func()
    assert result == "result"

    # Should have recorded timing
    global_metrics = get_metrics()
    assert "decorated_function" in str(global_metrics.points)


@pytest.mark.asyncio
async def test_measure_async_decorator():
    @measure("async_decorated_function")
    async def async_test_func():
        return "async_result"

    result = await async_test_func()
    assert result == "async_result"
