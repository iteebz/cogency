"""Test fixtures for cogency tests."""

from unittest.mock import Mock

import pytest

from cogency.core.result import Ok

# Force pytest-asyncio to load
pytest_plugins = ["pytest_asyncio"]


@pytest.fixture
def mock_llm():
    """Mock LLM provider for testing - canonical pattern."""
    provider = Mock()

    # Standard generation - async function that returns Result
    async def mock_generate(*args, **kwargs):
        return Ok("Test response")

    provider.generate = Mock(side_effect=mock_generate)

    # Streaming support with proper async generator
    provider.stream = None  # Disabled by default

    # WebSocket support for resume mode
    provider.resumable = False  # Disabled by default

    # Create a consistent session object for connect/close matching
    mock_session = Mock()

    async def mock_connect(*args, **kwargs):
        return mock_session

    async def mock_close(*args, **kwargs):
        return True

    provider.connect = Mock(side_effect=mock_connect, return_value=mock_session)
    provider.close = Mock(side_effect=mock_close)
    provider.receive = Mock(side_effect=mock_generator(["mock_token"]))

    return provider


@pytest.fixture
def mock_storage():
    """Mock storage for all tests - canonical pattern."""
    return Mock()


@pytest.fixture
def mock_xml_response():
    """Standard XML response for testing."""
    return """<thinking>
Processing request.
</thinking>

<response>
Test response
</response>"""


def mock_generator(items):
    """Create async generator factory for mocking.

    CANONICAL PATTERN: Eliminates async generator mocking ceremony.

    THE PROBLEM:
        # ❌ BROKEN - returns dead coroutine
        async def mock_gen():
            yield "item1"
        mock.return_value = mock_gen()  # Called once, returns coroutine

    THE SOLUTION:
        # ✅ WORKING - returns fresh generator each call
        mock.side_effect = mock_generator(["item1", "item2"])

    EXAMPLES:
        # Simple tokens
        mock_llm.receive.side_effect = mock_generator(["token1", "token2"])

        # Stream events
        mock_stream.side_effect = mock_generator([
            {"type": "respond", "content": "response"}
        ])

        # With fixture
        def test_something(mock_generator):
            mock.side_effect = mock_generator(["item1", "item2"])
    """

    async def async_generator():
        for item in items:
            yield item

    return lambda *args, **kwargs: async_generator()


@pytest.fixture
def mock_stream_events():
    """Mock stream events factory."""
    return mock_generator([{"type": "respond", "content": "Test response"}])


@pytest.fixture
def mock_websocket_tokens():
    """Mock WebSocket token stream factory."""
    return mock_generator(["token1", "token2", "token3"])


@pytest.fixture
def mock_consciousness_stream():
    """Mock consciousness stream for agent tests."""
    return mock_generator([{"type": "respond", "content": "Test response"}])


# Pytest fixture is just ceremony - direct import is cleaner
