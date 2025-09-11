import pytest

from cogency.core.protocols import Event
from cogency.lib.llms.interrupt import interruptible


@pytest.mark.asyncio
async def test_interruptible_graceful_termination():
    """@interruptible emits EXECUTE on any exception for graceful stream termination."""

    @interruptible
    async def stream(self):
        yield "chunk 1"
        yield "chunk 2"
        raise ValueError("Stream interrupted")
        yield "unreachable"

    events = []
    async for chunk in stream(None):
        events.append(chunk)

    # Stream continues normally until exception, then emits EXECUTE for graceful termination
    assert events == ["chunk 1", "chunk 2", Event.EXECUTE.delimiter]

    # Verify behavior with interruption exceptions (should re-raise)
    @interruptible
    async def interrupted_stream(self):
        yield "data"
        raise KeyboardInterrupt()

    events = []
    with pytest.raises(KeyboardInterrupt):
        async for chunk in interrupted_stream(None):
            events.append(chunk)

    assert events == ["data", Event.EXECUTE.delimiter]
