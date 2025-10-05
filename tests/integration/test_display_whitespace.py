import pytest

from cogency import Agent
from cogency.cli.display import Renderer


@pytest.mark.asyncio
async def test_chunks_with_leading_newlines(mock_llm, mock_tool):
    """Chunks with leading \n should not create visual whitespace."""
    protocol_tokens = [
        "§think: first",
        "\nsecond\n",
        "§respond: answer",
        "\nmore\n",
        "§end\n",
    ]

    llm = mock_llm.set_response_tokens(protocol_tokens)
    agent = Agent(llm=llm, tools=[mock_tool], mode="replay", max_iterations=1)
    events = [event async for event in agent("Test", chunks=True)]

    think_events = [e for e in events if e["type"] == "think"]
    respond_events = [e for e in events if e["type"] == "respond"]

    assert len(think_events) >= 2
    assert len(respond_events) >= 2

    # Chunks should preserve raw content
    think_contents = [e["content"] for e in think_events]
    assert any("\n" in c for c in think_contents)


@pytest.mark.asyncio
async def test_renderer_strips_leading_whitespace():
    """Renderer should strip leading whitespace from chunks to avoid boundaries."""
    renderer = Renderer()
    
    # Simulate think events with leading newlines
    events = [
        {"type": "think", "content": "first"},
        {"type": "think", "content": "\nsecond"},
        {"type": "think", "content": "\nthird"},
    ]

    output = []
    
    class MockPrint:
        def __call__(self, *args, **kwargs):
            output.append("".join(str(a) for a in args))
    
    import builtins
    original_print = builtins.print
    builtins.print = MockPrint()
    
    try:
        async def event_stream():
            for e in events:
                yield e
        
        await renderer.render_stream(event_stream())
    finally:
        builtins.print = original_print
    
    rendered = "".join(output)
    
    # Should not have double newlines or leading newline after state transition
    assert "\n\n" not in rendered
    assert not rendered.startswith("\n")
