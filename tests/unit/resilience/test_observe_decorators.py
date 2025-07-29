"""Test observe decorators functionality."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from cogency.decorators import is_observe_enabled, observe, set_observe_enabled
from cogency.monitoring.metrics import get_metrics
from cogency.state import State


@pytest.fixture
def test_state():
    """Create test state for decorator tests."""
    return State(query="test query", user_id="test_user", iteration=1, react_mode="fast")


@pytest.fixture(autouse=True)
def reset_observability():
    """Reset observability settings before each test."""
    # Store original state
    original_enabled = is_observe_enabled()

    # Reset for test
    set_observe_enabled(False)
    get_metrics().reset()

    yield

    # Restore original state
    set_observe_enabled(original_enabled)
    get_metrics().reset()


class TestObserveDecorators:
    """Test the observe decorator functionality."""

    @pytest.mark.asyncio
    async def test_observe_disabled_passthrough(self, test_state):
        """Test observe decorator passes through when disabled."""
        set_observe_enabled(False)

        @observe.preprocess()
        async def test_func(state):
            return f"processed: {state.query}"

        result = await test_func(test_state)
        assert result == "processed: test query"

        # Should have no metrics
        metrics = get_metrics()
        assert len(metrics.counters) == 0
        assert len(metrics.points) == 0

    @pytest.mark.asyncio
    async def test_observe_enabled_collects_metrics(self, test_state):
        """Test observe decorator collects metrics when enabled."""
        set_observe_enabled(True)

        @observe.preprocess()
        async def test_func(state):
            return f"processed: {state.query}"

        result = await test_func(test_state)
        assert result == "processed: test query"

        # Should have metrics
        metrics = get_metrics()

        # Check counters
        execution_key = "preprocessing.executions#iteration=1,phase=preprocessing,react_mode=fast"
        success_key = "preprocessing.success#iteration=1,phase=preprocessing,react_mode=fast"

        assert execution_key in metrics.counters
        assert success_key in metrics.counters
        assert metrics.counters[execution_key] == 1.0
        assert metrics.counters[success_key] == 1.0

        # Check duration histogram
        duration_key = "preprocessing.duration#iteration=1,phase=preprocessing,react_mode=fast"
        assert duration_key in metrics.points
        assert len(metrics.points[duration_key]) == 1

    @pytest.mark.asyncio
    async def test_observe_error_metrics(self, test_state):
        """Test observe decorator collects error metrics."""
        set_observe_enabled(True)

        @observe.reason()
        async def failing_func(state):
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            await failing_func(test_state)

        # Should have error metrics
        metrics = get_metrics()

        execution_key = "reasoning.executions#iteration=1,phase=reasoning,react_mode=fast"
        error_key = (
            "reasoning.errors#error_type=ValueError,iteration=1,phase=reasoning,react_mode=fast"
        )

        assert execution_key in metrics.counters
        assert error_key in metrics.counters
        assert metrics.counters[execution_key] == 1.0
        assert metrics.counters[error_key] == 1.0

        # Should not have success metric
        success_key = "reasoning.success#iteration=1,phase=reasoning,react_mode=fast"
        assert success_key not in metrics.counters

    @pytest.mark.asyncio
    async def test_observe_result_size_metrics(self, test_state):
        """Test observe decorator collects result size metrics."""
        set_observe_enabled(True)

        @observe.act()
        async def test_func(state):
            return "a" * 100  # 100 character result

        result = await test_func(test_state)
        assert len(result) == 100

        # Should have result size histogram
        metrics = get_metrics()
        size_key = "tool_execution.result_size#iteration=1,phase=tool_execution,react_mode=fast"

        assert size_key in metrics.points
        assert len(metrics.points[size_key]) == 1
        assert metrics.points[size_key][0].value == 100.0

    @pytest.mark.asyncio
    async def test_observe_different_phases(self, test_state):
        """Test different observe decorators create phase-specific metrics."""
        set_observe_enabled(True)

        @observe.preprocess()
        async def preprocess_func(state):
            return "preprocessed"

        @observe.respond()
        async def respond_func(state):
            return "responded"

        await preprocess_func(test_state)
        await respond_func(test_state)

        metrics = get_metrics()

        # Should have metrics for both phases
        preprocess_key = "preprocessing.executions#iteration=1,phase=preprocessing,react_mode=fast"
        respond_key = "response.executions#iteration=1,phase=response,react_mode=fast"

        assert preprocess_key in metrics.counters
        assert respond_key in metrics.counters
        assert metrics.counters[preprocess_key] == 1.0
        assert metrics.counters[respond_key] == 1.0

    @pytest.mark.asyncio
    async def test_observe_no_state_context(self):
        """Test observe decorator handles missing state gracefully."""
        set_observe_enabled(True)

        @observe.generic()
        async def test_func(data):
            return f"processed: {data}"

        result = await test_func("test data")
        assert result == "processed: test data"

        # Should have metrics with unknown tags
        metrics = get_metrics()
        generic_key = "generic.executions#iteration=0,phase=generic,react_mode=unknown"

        assert generic_key in metrics.counters
        assert metrics.counters[generic_key] == 1.0

    @pytest.mark.asyncio
    async def test_observe_state_from_kwargs(self, test_state):
        """Test observe decorator extracts state from kwargs."""
        set_observe_enabled(True)

        @observe.preprocess()
        async def test_func(data, state=None):
            return f"processed: {data}"

        result = await test_func("test", state=test_state)
        assert result == "processed: test"

        # Should have metrics with correct state context
        metrics = get_metrics()
        key = "preprocessing.executions#iteration=1,phase=preprocessing,react_mode=fast"

        assert key in metrics.counters
        assert metrics.counters[key] == 1.0


class TestObservabilityControl:
    """Test observability control functions."""

    def test_observe_enabled_default_false(self):
        """Test observe decorators are disabled by default."""
        assert is_observe_enabled() is False

    def test_set_observe_enabled(self):
        """Test setting observe enabled flag."""
        set_observe_enabled(True)
        assert is_observe_enabled() is True

        set_observe_enabled(False)
        assert is_observe_enabled() is False
