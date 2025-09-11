"""Essential test machinery - WebSocket mocking and async generators."""

from unittest.mock import AsyncMock, Mock

import pytest

from cogency.core.result import Ok

pytest_plugins = ["pytest_asyncio"]


def mock_generator(items):
    """Fresh async generator per call - eliminates dead coroutine ceremony."""

    async def async_gen():
        for item in items:
            yield item

    return lambda *args, **kwargs: async_gen()


@pytest.fixture
def mock_llm():
    """Complete LLM mock with WebSocket support."""
    llm = Mock()

    # Core generation
    llm.generate = AsyncMock(return_value=Ok("Test response"))

    # WebSocket operations
    llm.connect = AsyncMock(return_value=Mock())
    llm.close = AsyncMock()
    llm.receive = Mock(side_effect=mock_generator(["token1", "token2"]))
    llm.resumable = False

    # Stream generation
    async def mock_stream(*args, **kwargs):
        yield "§RESPOND"
        yield "Test response"
        yield "§END"

    llm.stream = Mock(side_effect=lambda *args, **kwargs: mock_stream())

    return llm
