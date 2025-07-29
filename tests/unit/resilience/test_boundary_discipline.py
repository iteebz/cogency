"""Test boundary discipline - proper Result unwrapping in decorated functions."""

from unittest.mock import Mock

import pytest
from resilient_result import Err, Ok, Result, Retry, resilient, unwrap

from cogency.state import State


def test_unwrap_success():
    """Test unwrap extracts data from Ok Results."""
    result = Ok("test data")
    assert unwrap(result) == "test data"


def test_unwrap_failure():
    """Test unwrap raises exception for Err Results."""
    result = Err("test error")
    with pytest.raises(Exception):
        unwrap(result)


def test_unwrap_standard():
    """Test standard unwrap behavior with Result objects."""
    # Standard unwrap expects Result objects - proper boundary discipline
    assert unwrap(Ok("test")) == "test"
    assert unwrap(Ok(42)) == 42
    assert unwrap(Ok(None)) is None


@pytest.mark.asyncio
async def test_boundary_discipline_in_decorated_function():
    """Test proper unwrapping inside @agent decorated functions."""

    @resilient(retry=Retry.api())
    async def mock_llm_call():
        # Simulate LLM returning Result
        return Ok("LLM response")

    # This simulates how nodes use unwrap inside decorated functions
    @resilient(retry=Retry.api())
    async def process_with_unwrap():
        llm_result = await mock_llm_call()
        # Boundary discipline: unwrap the Result inside the decorated function
        raw_response = unwrap(llm_result)
        return f"processed: {raw_response}"

    result = await process_with_unwrap()
    assert result.success
    assert result.data == "processed: LLM response"


@pytest.mark.asyncio
async def test_unwrap_with_state_object():
    """Test unwrap works correctly with State objects in decorated functions."""

    @resilient(retry=Retry.api())
    async def node_function(state):
        # Simulate parsing that returns Result
        parse_result = Ok({"tool_calls": ["test_call"]})

        # Boundary discipline: unwrap inside the decorated function
        parsed_data = unwrap(parse_result)

        # Update state with unwrapped data
        state.tool_calls = parsed_data["tool_calls"]
        return state

    # Create test state
    state = State(query="test query")

    result_state = await node_function(state)
    assert result_state.success
    assert result_state.data.tool_calls == ["test_call"]


def test_unwrap_utility():
    """Test standard unwrap utility with Result objects."""
    # Test with Result objects - proper boundary discipline
    assert unwrap(Ok("data")) == "data"

    # Test error unwrapping
    with pytest.raises(ValueError):
        unwrap(Err("error message"))
