"""Profiling tests - resource monitoring logic."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from cogency.observe.profiling import (
    ProfileMetrics,
    Profiler,
    get_profiler,
    profile_async,
    profile_sync,
)


@pytest.fixture
def profiler():
    p = get_profiler()
    p.metrics = []  # Clear metrics before each test
    return p


@pytest.fixture
def profile_metrics():
    return ProfileMetrics(
        operation_name="test_op",
        start_time=1.0,
        end_time=2.0,
        duration=1.0,
        memory_before=100.0,
        memory_after=120.0,
        memory_delta=20.0,
        cpu_percent=50.0,
        peak_memory=125.0,
        metadata={"test": True},
    )


@pytest.mark.asyncio
async def test_context(profiler):
    with patch("psutil.Process") as mock_process:
        mock_process.return_value.memory_info.return_value.rss = 100 * 1024 * 1024
        mock_process.return_value.cpu_percent.return_value = 25.0

        async with profiler.profile("test_operation"):
            await asyncio.sleep(0.01)

    assert len(profiler.metrics) == 1
    metric = profiler.metrics[0]
    assert metric.operation_name == "test_operation"
    assert metric.duration > 0


def test_bottlenecks(profiler, profile_metrics):
    profiler.metrics = [profile_metrics]

    # Test with default thresholds
    bottlenecks = profiler.get_bottlenecks(threshold_duration=0.5, threshold_memory=10.0)
    assert len(bottlenecks) == 1
    assert bottlenecks[0].operation_name == "test_op"

    # Test with high thresholds
    bottlenecks = profiler.get_bottlenecks(threshold_duration=2.0, threshold_memory=50.0)
    assert len(bottlenecks) == 0


def test_empty(profiler):
    summary = profiler.summary()
    assert summary == {"message": "No profiling data available"}


def test_summary(profiler, profile_metrics):
    profiler.metrics = [profile_metrics]

    summary = profiler.summary()
    assert summary["total_operations"] == 1
    assert summary["total_duration"] == 1.0
    assert "test_op" in summary["operations"]

    op_summary = summary["operations"]["test_op"]
    assert op_summary["count"] == 1
    assert op_summary["avg_duration"] == 1.0
    assert op_summary["max_duration"] == 1.0


def test_json(profiler, profile_metrics, tmp_path):
    profiler.metrics = [profile_metrics]

    filepath = tmp_path / "profile.json"
    profiler.to_json(str(filepath))

    assert filepath.exists()

    import json

    with open(filepath) as f:
        data = json.load(f)

    assert "summary" in data
    assert "bottlenecks" in data
    assert "detailed_metrics" in data


@pytest.mark.asyncio
async def test_async():
    async def test_func(x, y):
        await asyncio.sleep(0.01)
        return x + y

    result = await profile_async("async_test", test_func, 1, 2)
    assert result == 3

    global_profiler = get_profiler()
    assert len(global_profiler.metrics) > 0


def test_sync():
    def test_func(x, y):
        return x * y

    result = profile_sync("sync_test", test_func, 3, 4)
    assert result == 12


def test_profiler():
    cogency_profiler = Profiler()
    assert cogency_profiler.profiler is get_profiler()


@pytest.mark.asyncio
async def test_methods():
    cogency_profiler = Profiler()

    async def mock_func():
        return "test"

    # Test all profiling methods
    result = await cogency_profiler.profile_reasoning_loop(mock_func)
    assert result == "test"

    result = await cogency_profiler.profile_tools(mock_func)
    assert result == "test"

    result = await cogency_profiler.profile_memory(mock_func)
    assert result == "test"

    result = await cogency_profiler.profile_llm(mock_func)
    assert result == "test"
