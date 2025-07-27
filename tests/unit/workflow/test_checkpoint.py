"""Test checkpoint decorator - context-driven checkpointing."""

from unittest.mock import Mock

import pytest

from cogency.context import Context
from cogency.resilience.checkpoint import checkpoint
from cogency.state import State


@pytest.mark.asyncio
async def test_checkpoint_decorator_passthrough():
    """Test checkpoint decorator works as passthrough when checkpointing disabled."""

    @checkpoint("test_checkpoint")
    async def test_function(state):
        return f"processed: {state.query}"

    # Create mock state
    context = Context("test query")
    state = State(context=context, query="test query")

    result = await test_function(state)
    assert result == "processed: test query"


@pytest.mark.asyncio
async def test_checkpoint_decorator_with_interruptible():
    """Test checkpoint decorator with interruptible flag."""

    @checkpoint("test_checkpoint", interruptible=True)
    async def test_function(state):
        return f"interruptible: {state.query}"

    # Create mock state
    context = Context("test query")
    state = State(context=context, query="test query")

    result = await test_function(state)
    assert result == "interruptible: test query"


@pytest.mark.asyncio
async def test_checkpoint_decorator_preserves_function_metadata():
    """Test checkpoint decorator preserves original function metadata."""

    @checkpoint("test_checkpoint")
    async def test_function_with_docstring(state):
        """This is a test function."""
        return "success"

    assert test_function_with_docstring.__name__ == "test_function_with_docstring"
    assert "This is a test function." in test_function_with_docstring.__doc__
