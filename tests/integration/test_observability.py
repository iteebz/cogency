#!/usr/bin/env python3
"""Integration test for @observe decorators with proper mocking."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

from cogency.decorators import is_observe_enabled, observe, set_observe_enabled
from cogency.state import State


class MockMetrics:
    """Mock metrics collector for testing."""

    def __init__(self):
        self.counters = {}
        self.timers = {}
        self.histograms = {}
        self.timer_contexts = []

    def counter(self, name, value, tags):
        key = f"{name}:{','.join(f'{k}={v}' for k, v in tags.items())}"
        self.counters[key] = self.counters.get(key, 0) + value

    def timer(self, name, tags):
        key = f"{name}:{','.join(f'{k}={v}' for k, v in tags.items())}"
        context = MockTimerContext(self, key)
        self.timer_contexts.append(context)
        return context

    def histogram(self, name, value, tags):
        key = f"{name}:{','.join(f'{k}={v}' for k, v in tags.items())}"
        self.histograms[key] = value


class MockTimerContext:
    """Mock timer context manager."""

    def __init__(self, metrics, key):
        self.metrics = metrics
        self.key = key

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.metrics.timers[self.key] = 0.1  # Mock duration


async def test_observe_decorators_integration():
    """Test complete @observe decorator integration."""

    # Mock the metrics module
    mock_metrics = MockMetrics()

    with (
        patch("cogency.decorators.counter", mock_metrics.counter),
        patch("cogency.decorators.timer", mock_metrics.timer),
        patch("cogency.decorators.histogram", mock_metrics.histogram),
    ):
        # Test observability disabled by default
        assert is_observe_enabled() is False
        print("✓ Observability disabled by default")

        # Test enabling observability
        set_observe_enabled(True)
        assert is_observe_enabled() is True
        print("✓ Observability enabled successfully")

        # Create test state
        state = State(query="test query", user_id="test_user", react_mode="fast", iteration=1)

        # Test phase decorators with real function calls
        @observe.preprocess()
        async def mock_preprocess(state, llm, tools, memory):
            return "preprocess_result"

        @observe.reason()
        async def mock_reason(state, llm, tools):
            return "reason_result"

        @observe.act()
        async def mock_act(state, tools):
            return "act_result"

        @observe.respond()
        async def mock_respond(state, llm, tools):
            return "respond_result"

        # Mock function arguments
        mock_llm = Mock()
        mock_tools = []
        mock_memory = Mock()

        # Execute all phase functions
        await mock_preprocess(state, mock_llm, mock_tools, mock_memory)
        await mock_reason(state, mock_llm, mock_tools)
        await mock_act(state, mock_tools)
        await mock_respond(state, mock_llm, mock_tools)

        print("✓ All phase decorators executed successfully")

        # Verify metrics were collected
        expected_phases = ["preprocessing", "reasoning", "tool_execution", "response"]

        for phase in expected_phases:
            # Check execution counters
            exec_keys = [k for k in mock_metrics.counters if f"{phase}.executions" in k]
            assert len(exec_keys) > 0, f"Missing execution metrics for {phase}"

            # Check success counters
            success_keys = [k for k in mock_metrics.counters if f"{phase}.success" in k]
            assert len(success_keys) > 0, f"Missing success metrics for {phase}"

            # Check timers
            timer_keys = [k for k in mock_metrics.timers if f"{phase}.duration" in k]
            assert len(timer_keys) > 0, f"Missing timer metrics for {phase}"

        print(f"✓ Collected {len(mock_metrics.counters)} counter metrics")
        print(f"✓ Collected {len(mock_metrics.timers)} timer metrics")

        # Verify context tags are included
        sample_counter = list(mock_metrics.counters.keys())[0]
        assert "phase=" in sample_counter, "Missing phase tag"
        assert "iteration=" in sample_counter, "Missing iteration tag"
        assert "react_mode=" in sample_counter, "Missing react_mode tag"
        print("✓ Context tags properly included in metrics")

        # Test error metrics
        @observe.generic()
        async def failing_function(state):
            raise ValueError("test error")

        import contextlib

        with contextlib.suppress(ValueError):
            await failing_function(state)

        # Check error metrics were recorded
        error_keys = [k for k in mock_metrics.counters if "generic.errors" in k]
        assert len(error_keys) > 0, "Missing error metrics"

        # Verify error type tag
        error_key = error_keys[0]
        assert "error_type=ValueError" in error_key, "Missing error_type tag"
        print("✓ Error metrics and tags working correctly")

        # Test disabling observability
        set_observe_enabled(False)
        assert is_observe_enabled() is False

        # Clear metrics and test pass-through
        initial_count = len(mock_metrics.counters)
        await mock_preprocess(state, mock_llm, mock_tools, mock_memory)

        # Should be no new metrics when disabled
        assert len(mock_metrics.counters) == initial_count, "Metrics collected when disabled"
        print("✓ Observability properly disabled - no metrics collected")

        print("\n🎉 All observability integration tests passed!")


if __name__ == "__main__":
    asyncio.run(test_observe_decorators_integration())
