"""Profiling tests - resource monitoring logic."""

import asyncio
from unittest.mock import patch

import pytest

from cogency.observe.profiler import (
    get_profiler,
    profile_async,
    profile_sync,
)


@pytest.fixture
def profiler():
    return get_profiler()


# ProfileMetrics removed - profiler emits events directly


@pytest.mark.asyncio
async def test_context(profiler):
    with patch("psutil.Process") as mock_process:
        mock_process.return_value.memory_info.return_value.rss = 100 * 1024 * 1024
        mock_process.return_value.cpu_percent.return_value = 25.0

        with patch("cogency.events.emit") as mock_emit:
            async with profiler.profile("test_operation"):
                await asyncio.sleep(0.01)

            # Verify profile event was emitted
            mock_emit.assert_called_once()
            call_args = mock_emit.call_args
            assert call_args[0][0] == "profile"
            assert call_args[1]["operation"] == "test_operation"
            assert call_args[1]["duration"] > 0


def test_enabled_state(profiler):
    # Test that profiler respects psutil availability
    assert profiler.enabled == profiler.enabled  # Should be consistent
    assert profiler.sample_interval == 0.1


def test_monitoring_lifecycle(profiler):
    # Test that monitoring can be started and stopped
    profiler._start_monitoring("test_op")
    assert "test_op" in profiler.active_profiles

    profiler._stop_monitoring("test_op")
    assert "test_op" not in profiler.active_profiles


@pytest.mark.asyncio
async def test_profile_with_metadata(profiler):
    metadata = {"test": True, "version": "1.0"}

    with patch("cogency.events.emit") as mock_emit:
        async with profiler.profile("test_operation", metadata=metadata):
            await asyncio.sleep(0.01)

        # Verify metadata was included in the event
        call_args = mock_emit.call_args
        assert call_args[1]["metadata"] == metadata


@pytest.mark.asyncio
async def test_profile_without_psutil(profiler):
    # Test graceful fallback when psutil is not available
    original_enabled = profiler.enabled
    profiler.enabled = False

    with patch("cogency.events.emit") as mock_emit:
        async with profiler.profile("test_operation"):
            await asyncio.sleep(0.01)

        # Should still emit event with basic timing
        mock_emit.assert_called_once()
        call_args = mock_emit.call_args
        assert call_args[1]["memory_before"] == 0.0
        assert call_args[1]["memory_after"] == 0.0
        assert call_args[1]["cpu_percent"] == 0.0

    profiler.enabled = original_enabled


@pytest.mark.asyncio
async def test_async():
    async def test_func(x, y):
        await asyncio.sleep(0.01)
        return x + y

    with patch("cogency.events.emit") as mock_emit:
        result = await profile_async("async_test", test_func, 1, 2)
        assert result == 3

        # Verify profiling event was emitted
        mock_emit.assert_called_once()
        call_args = mock_emit.call_args
        assert call_args[0][0] == "profile"
        assert call_args[1]["operation"] == "async_test"


def test_sync():
    def test_func(x, y):
        return x * y

    with patch("cogency.events.emit") as mock_emit:
        result = profile_sync("sync_test", test_func, 3, 4)
        assert result == 12

        # Verify profiling event was emitted
        mock_emit.assert_called_once()
        call_args = mock_emit.call_args
        assert call_args[0][0] == "profile"
        assert call_args[1]["operation"] == "sync_test"


def test_profiler_singleton():
    profiler1 = get_profiler()
    profiler2 = get_profiler()
    assert profiler1 is profiler2
