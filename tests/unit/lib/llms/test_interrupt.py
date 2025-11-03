import asyncio
from unittest.mock import patch

import pytest

from cogency.lib.llms.interrupt import interruptible


class MockLLM:
    def __init__(self):
        self.name = "MockLLM"

    @interruptible
    async def mock_async_generator(self):
        yield "chunk1"
        raise RuntimeError("Test Error")
        yield "chunk2"  # This should not be reached

    @interruptible
    async def mock_async_generator_no_error(self):
        yield "chunk1"
        yield "chunk2"


@pytest.mark.asyncio
async def test_re_raises_exception():
    mock_llm = MockLLM()
    with patch("cogency.lib.llms.interrupt.logger.error") as mock_logger_error:
        with pytest.raises(RuntimeError, match="Test Error"):
            async for _ in mock_llm.mock_async_generator():
                pass
        mock_logger_error.assert_called_once_with("MockLLM error: Test Error")


@pytest.mark.asyncio
async def test_yields_chunks_without_error():
    mock_llm = MockLLM()
    collected_chunks = []
    async for chunk in mock_llm.mock_async_generator_no_error():
        collected_chunks.append(chunk)
    assert collected_chunks == ["chunk1", "chunk2"]


@pytest.mark.asyncio
async def test_handles_keyboard_interrupt():
    mock_llm = MockLLM()

    @interruptible
    async def generator_with_keyboard_interrupt(self):
        yield "chunk1"
        raise KeyboardInterrupt

    with patch("cogency.lib.llms.interrupt.logger.info") as mock_logger_info:
        with pytest.raises(KeyboardInterrupt):
            async for _ in generator_with_keyboard_interrupt(mock_llm):
                pass
        mock_logger_info.assert_called_once_with("MockLLM interrupted by user (Ctrl+C)")


@pytest.mark.asyncio
async def test_handles_cancelled_error():
    mock_llm = MockLLM()

    @interruptible
    async def generator_with_cancelled_error(self):
        yield "chunk1"
        raise asyncio.CancelledError

    with patch("cogency.lib.llms.interrupt.logger.debug") as mock_logger_debug:
        with pytest.raises(asyncio.CancelledError):
            async for _ in generator_with_cancelled_error(mock_llm):
                pass
        mock_logger_debug.assert_called_once_with("MockLLM cancelled")
