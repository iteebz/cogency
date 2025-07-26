"""Essential boundary discipline tests - architectural contract enforcement."""

from unittest.mock import Mock

import pytest

from cogency.resilience import Err, Ok, Result, safe
from cogency.resilience.patterns import unwrap_result
from cogency.state import State


class TestBoundaryContract:
    """Core contract: Result objects NEVER leak beyond decorator boundary."""

    @pytest.mark.asyncio
    async def test_all_decorators_unwrap_consistently(self):
        """CRITICAL: All decorators must unwrap Results to domain objects."""

        @safe.memory()
        async def memory_op(state):
            return Ok("memory_result")

        @safe.reasoning()
        async def reasoning_op(state):
            return Ok("reasoning_result")

        @safe.act()
        async def act_op(state):
            return Ok("act_result")

        state = Mock(spec=State)

        # All must return unwrapped domain objects
        memory_result = await memory_op(state)
        reasoning_result = await reasoning_op(state)
        act_result = await act_op(state)

        # ARCHITECTURAL CONTRACT: No Result leakage
        assert not isinstance(memory_result, Result)
        assert not isinstance(reasoning_result, Result)
        assert not isinstance(act_result, Result)

        # Clean domain objects only
        assert memory_result == "memory_result"
        assert reasoning_result == "reasoning_result"
        assert act_result == "act_result"

    @pytest.mark.asyncio
    async def test_error_unwrapping_preserves_exceptions(self):
        """CRITICAL: Errors must unwrap to exceptions, preserving chains."""

        @safe.memory(retries=1)
        async def failing_op(state):
            original = ConnectionError("network failed")
            try:
                raise ValueError("retry failed") from original
            except ValueError as chained_error:
                return Err(chained_error)

        state = Mock(spec=State)

        # Should raise unwrapped exception with preserved chain
        with pytest.raises(ValueError, match="retry failed") as exc_info:
            await failing_op(state)

        # Exception chain MUST be preserved for debugging
        assert isinstance(exc_info.value.__cause__, ConnectionError)
        assert "network failed" in str(exc_info.value.__cause__)

    def test_centralized_unwrap_logic(self):
        """CRITICAL: unwrap_result is single source of truth."""

        # Success case: Ok -> domain object
        success = Ok("clean_data")
        assert unwrap_result(success) == "clean_data"
        assert not isinstance(unwrap_result(success), Result)

        # Error case: Err -> exception
        error = Err(ValueError("domain_error"))
        with pytest.raises(ValueError, match="domain_error"):
            unwrap_result(error)

        # Passthrough: non-Result -> unchanged
        domain_obj = {"state": "data"}
        assert unwrap_result(domain_obj) is domain_obj


class TestRegressionPrevention:
    """High-signal regression tests - these MUST NOT break."""

    @pytest.mark.asyncio
    async def test_end_to_end_boundary_integrity(self):
        """REGRESSION GUARD: Full chain must maintain clean boundaries."""

        @safe.memory()
        async def memory_layer(state):
            return Ok({"retrieved": "data"})

        @safe.reasoning()
        async def reasoning_layer(state):
            # Domain operations should never see Results
            memory_data = await memory_layer(state)
            assert not isinstance(memory_data, Result), "BOUNDARY VIOLATION: Result leaked!"
            return Ok(state)

        @safe.act()
        async def action_layer(state):
            reasoning_result = await reasoning_layer(state)
            assert not isinstance(reasoning_result, Result), "BOUNDARY VIOLATION: Result leaked!"
            return Ok({"completed": True})

        state = Mock(spec=State)
        final_result = await action_layer(state)

        # Final result must be clean domain object
        assert not isinstance(final_result, Result)
        assert final_result == {"completed": True}

    def test_unwrap_state_false_internal_usage(self):
        """REGRESSION GUARD: Internal code can still use Results when needed."""

        @safe.memory(unwrap_state=False)
        async def internal_resilience_op(state):
            return Ok("internal_data")

        # Internal resilience code can work with Results directly
        async def test_internal():
            state = Mock(spec=State)
            result = await internal_resilience_op(state)
            assert isinstance(result, Result)
            assert result.success
            assert result.data == "internal_data"

        import asyncio

        asyncio.run(test_internal())


class TestArchitecturalLinchpin:
    """Document the pattern that keeps everything clean."""

    def test_boundary_pattern_documentation(self):
        """Living documentation of the Result boundary pattern."""

        # RULE 1: Domain code works with clean objects
        domain_data = "clean_state_object"
        assert not isinstance(domain_data, Result)

        # RULE 2: isinstance(Result) allowed ONLY in decorators/unwrap_result
        result_wrapper = Ok("data")
        assert isinstance(result_wrapper, Result)  # Only acceptable at boundary

        # RULE 3: Unwrapping is centralized and consistent
        unwrapped = unwrap_result(result_wrapper)
        assert unwrapped == "data"
        assert not isinstance(unwrapped, Result)

    def test_critical_regression_detector(self):
        """High-signal test that fails immediately if boundary breaks."""

        @safe.memory()
        async def test_function(state):
            return Ok("should_be_unwrapped")

        async def verify_boundary():
            state = Mock(spec=State)
            result = await test_function(state)

            # This assertion MUST pass - if it fails, the boundary is broken
            assert not isinstance(result, Result), (
                "CRITICAL REGRESSION: Result object leaked into domain layer! "
                "The automatic unwrap mechanism is broken."
            )

            return result == "should_be_unwrapped"

        import asyncio

        assert asyncio.run(verify_boundary())
