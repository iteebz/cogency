"""Shared test fixtures for cogency unit tests."""

import tempfile

import pytest

from cogency.state import AgentState

# Import all fixtures from decomposed modules
from .fixtures import (
    base_agent,
    in_memory_store,
    mock_llm,
    mock_tool,
    realistic_llm,
    tools,
    validation_schemas,
)


@pytest.fixture
def temp_dir():
    """Temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def agent_state():
    """Basic agent state."""
    return AgentState(query="test query")
