import pytest

from cogency import Agent


@pytest.mark.asyncio
async def test_streaming_no_chunks(mock_llm, mock_tool):
    protocol_tokens = [
        "§think: I need to call a tool.\n",
        '§call: {"name": "test_tool", "args": {"message": "hello world"}}\n',
        "§execute\n",
        "§respond: The tool completed successfully.\n",
        "§end\n",
    ]

    llm = mock_llm.set_response_tokens(protocol_tokens)
    agent = Agent(llm=llm, tools=[mock_tool], mode="replay", max_iterations=1)
    events = [event async for event in agent("Test query", chunks=False)]

    assert len(events) >= 2
    assert events[0]["type"] == "think"
    assert "need to call a tool" in events[0]["content"]
    assert events[1]["type"] == "call"
    assert events[2]["type"] == "result"
    assert "Tool executed: hello world" in events[2]["payload"]["outcome"]


@pytest.mark.asyncio
async def test_streaming_chunks(mock_llm, mock_tool):
    protocol_tokens = [
        "§think: Think",
        "ing...\n",
        '§call: {"name": "test_tool", "args": {"message": "test"}}\n',
        "§execute\n",
        "§respond: Done!\n",
        "§end\n",
    ]

    llm = mock_llm.set_response_tokens(protocol_tokens)
    agent = Agent(llm=llm, tools=[mock_tool], mode="replay", max_iterations=1)
    events = [event async for event in agent("Test query", chunks=True)]

    assert len(events) >= 5
    content_events = [e["content"] for e in events if e.get("content")]
    assert len(content_events) >= 3


@pytest.mark.asyncio
async def test_tool_execution(mock_llm, mock_tool):
    protocol_tokens = [
        '§call: {"name": "test_tool", "args": {"message": "integration test"}}\n',
        "§execute\n",
        "§respond: Tool call completed.\n",
        "§end\n",
    ]

    llm = mock_llm.set_response_tokens(protocol_tokens)
    agent = Agent(llm=llm, tools=[mock_tool], mode="replay", max_iterations=1)
    events = [event async for event in agent("Test query", chunks=False)]

    assert len(events) >= 2
    call_event = events[0]
    result_event = events[1]
    assert call_event["type"] == "call"
    assert result_event["type"] == "result"
    assert "Tool executed: integration test" in result_event["payload"]["outcome"]


@pytest.mark.asyncio
async def test_error_handling(mock_llm, mock_tool):
    protocol_tokens = [
        '§call: {"name": "failing_tool", "args": {}}\n',
        "§execute\n",
        "§respond: Handling error...\n",
        "§end\n",
    ]

    llm = mock_llm.set_response_tokens(protocol_tokens)
    failing_tool = mock_tool.configure(
        name="failing_tool", description="Tool that fails", should_fail=True
    )
    agent = Agent(llm=llm, tools=[failing_tool], mode="replay", max_iterations=1)

    with pytest.raises(RuntimeError, match="Stream execution failed"):
        [event async for event in agent("Test query", chunks=False)]


@pytest.mark.asyncio
async def test_persistence(mock_llm, mock_tool, mock_storage):
    protocol_tokens = [
        "§think: Thinking...\n",
        '§call: {"name": "test_tool", "args": {"message": "persist_test"}}\n',
        "§execute\n",
        "§respond: Response text\n",
        "§end\n",
    ]

    llm = mock_llm.set_response_tokens(protocol_tokens)
    agent = Agent(llm=llm, tools=[mock_tool], storage=mock_storage, mode="replay", max_iterations=1)
    events = [event async for event in agent("Test query", chunks=False)]

    assert len(events) >= 2
    assert any(e["type"] == "think" for e in events)
    assert any(e["type"] == "result" for e in events)
