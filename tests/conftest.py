"""Test fixtures for cogency tests."""

from unittest.mock import AsyncMock, Mock

import pytest

from cogency.lib.result import Ok


@pytest.fixture
def mock_llm():
    """Mock LLM provider for testing."""
    provider = Mock()
    provider.generate = AsyncMock(return_value=Ok("Test response"))
    # Explicitly disable streaming to force batch mode
    provider.stream = None
    return provider


@pytest.fixture
def mock_xml_response():
    """Standard XML response for testing."""
    return """<thinking>
Processing request.
</thinking>

<response>
Test response
</response>"""
