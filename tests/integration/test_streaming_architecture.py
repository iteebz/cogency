import pytest

from cogency import Agent, AgentError


@pytest.mark.asyncio
async def test_no_chunks(mock_llm, mock_tool):
    mock_tool_instance = mock_tool()
    protocol_tokens = [
        "<think>I need to call a tool.</think>",
        f'<execute>[{{"name": "{mock_tool_instance.name}", "args": {{"message": "hello world"}}}}]</execute>',
        "The tool completed successfully.",
    ]

    llm = mock_llm.set_response_tokens(protocol_tokens)
    agent = Agent(llm=llm, tools=[mock_tool_instance], mode="replay", max_iterations=1)
    events = [event async for event in agent("Test query", stream="event")]

    assert len(events) >= 5
    event_types = [e["type"] for e in events]

    # Verify user event first
    assert events[0]["type"] == "user"
    assert events[0]["content"] == "Test query"

    # Verify all core events present (order may vary in event mode)
    assert "think" in event_types
    assert "call" in event_types
    assert "execute" in event_types
    assert "result" in event_types

    # Verify think content
    think_event = next((e for e in events if e["type"] == "think"), None)
    assert think_event and "need to call a tool" in think_event["content"]

    result_event = next((e for e in events if e["type"] == "result"), None)
    assert result_event is not None
    assert result_event["payload"]["tools_executed"] == 1
    assert result_event["payload"]["success_count"] == 1
    assert "<results>" in result_event["content"]
    assert "test_tool" in result_event["content"]


@pytest.mark.asyncio
async def test_chunks(mock_llm, mock_tool):
    mock_tool_instance = mock_tool()
    protocol_tokens = [
        "<think>Think",
        "ing...</think>",
        f'<execute>[{{"name": "{mock_tool_instance.name}", "args": {{"message": "test"}}}}]</execute>',
        "Done!",
    ]

    llm = mock_llm.set_response_tokens(protocol_tokens)
    agent = Agent(llm=llm, tools=[mock_tool_instance], mode="replay", max_iterations=1)
    events = [event async for event in agent("Test query", stream="token")]

    assert len(events) >= 5
    content_events = [e["content"] for e in events if e.get("content")]
    assert len(content_events) >= 3


@pytest.mark.asyncio
async def test_tool_execution(mock_llm, mock_tool):
    mock_tool_instance = mock_tool()
    protocol_tokens = [
        f'<execute>[{{"name": "{mock_tool_instance.name}", "args": {{"message": "integration test"}}}}]</execute>',
        "Tool call completed.",
    ]

    llm = mock_llm.set_response_tokens(protocol_tokens)
    agent = Agent(llm=llm, tools=[mock_tool_instance], mode="replay", max_iterations=1)
    events = [event async for event in agent("Test query", stream="event")]

    assert len(events) >= 5
    assert events[0]["type"] == "user"
    call_event = events[1]
    execute_event = events[2]
    metric_event = events[3]
    result_event = events[4]
    assert call_event["type"] == "call"
    assert execute_event["type"] == "execute"
    assert metric_event["type"] == "metric"
    assert result_event["type"] == "result"

    assert result_event["payload"]["tools_executed"] == 1
    assert result_event["payload"]["success_count"] == 1
    assert "<results>" in result_event["content"]
    assert "test_tool" in result_event["content"]


@pytest.mark.asyncio
async def test_error_handling(mock_llm, mock_tool):
    failing_tool = mock_tool().configure(
        name="failing_tool", description="Tool that fails", should_fail=True
    )
    protocol_tokens = [
        f'<execute>[{{"name": "{failing_tool.name}", "args": {{}}}}]</execute>',
        "Handling error...",
    ]

    llm = mock_llm.set_response_tokens(protocol_tokens)
    agent = Agent(llm=llm, tools=[failing_tool], mode="replay", max_iterations=1)

    events = [event async for event in agent("Test query", stream="event")]
    result_events = [e for e in events if e["type"] == "result"]
    assert len(result_events) == 1
    assert result_events[0]["payload"]["failure_count"] == 1


@pytest.mark.asyncio
async def test_persistence(mock_llm, mock_tool, mock_storage):
    mock_tool_instance = mock_tool()
    protocol_tokens = [
        "<think>Thinking...</think>",
        f'<execute>[{{"name": "{mock_tool_instance.name}", "args": {{"message": "persist_test"}}}}]</execute>',
        "Response text",
    ]

    llm = mock_llm.set_response_tokens(protocol_tokens)
    agent = Agent(
        llm=llm, tools=[mock_tool_instance], storage=mock_storage, mode="replay", max_iterations=1
    )
    events = [event async for event in agent("Test query", stream="event")]

    assert len(events) >= 3
    assert any(e["type"] == "user" for e in events)
    assert any(e["type"] == "think" for e in events)
    assert any(e["type"] == "result" for e in events)


@pytest.mark.asyncio
async def test_event_taxonomy(mock_llm, mock_tool):
    """Verify complete event taxonomy with multi-iteration flow.

    With parser hardstop on </execute>, respond comes in iteration 2.
    This tests the full nominal path:
    - Iter 1: think → call tool → execute (hardstop)
    - Tool executes with result
    - Iter 2: (with tool result in context) → respond
    """
    mock_tool_instance = mock_tool()
    iteration_tokens = [
        [
            "<think>reasoning</think>",
            f'<execute>[{{"name": "{mock_tool_instance.name}", "args": {{"message": "test"}}}}]</execute>',
        ],
        [
            "result processed",
        ],
    ]

    iteration_idx = [0]

    class MultiIterMockLLM:
        http_model = "test"

        async def generate(self, messages):
            return ""

        async def stream(self, messages):
            tokens = iteration_tokens[min(iteration_idx[0], len(iteration_tokens) - 1)]
            iteration_idx[0] += 1
            for token in tokens:
                yield token

    agent = Agent(
        llm=MultiIterMockLLM(), tools=[mock_tool_instance], mode="replay", max_iterations=2
    )
    events = [event async for event in agent("Test", stream="event")]

    event_types = [e["type"] for e in events]

    # Verify all core events present
    assert "user" in event_types
    assert "think" in event_types
    assert "call" in event_types
    assert "execute" in event_types
    assert "result" in event_types
    assert "respond" in event_types
    assert "metric" in event_types

    # Verify order boundaries
    user_idx = event_types.index("user")
    execute_idx = event_types.index("execute")
    result_idx = event_types.index("result")
    respond_idx = event_types.index("respond")

    # High-level ordering: user first, execution happens before respond
    assert user_idx < execute_idx
    assert execute_idx < result_idx
    assert result_idx < respond_idx


@pytest.mark.asyncio
async def test_generate_mode(mock_llm, mock_tool):
    """Parser accepts complete string from LLM.generate()."""

    completion = "<think>analyzing request</think>The answer is 42"

    class GenerateMockLLM:
        async def generate(self, messages):
            return completion

        async def stream(self, messages):
            for token in completion:
                yield token

    agent = Agent(llm=GenerateMockLLM(), tools=[mock_tool()], mode="replay", max_iterations=1)
    events = [event async for event in agent("Test", stream=None)]

    event_types = [e["type"] for e in events]

    assert "user" in event_types
    assert "think" in event_types
    assert "respond" in event_types

    think_event = next(e for e in events if e["type"] == "think")
    assert "analyzing request" in think_event["content"]

    respond_event = next(e for e in events if e["type"] == "respond")
    assert "42" in respond_event["content"]
