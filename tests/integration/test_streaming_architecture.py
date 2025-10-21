import pytest

from cogency import Agent, AgentError


@pytest.mark.asyncio
async def test_no_chunks(mock_llm, mock_tool):
    protocol_tokens = [
        "§think: I need to call a tool.\n",
        '§call: {"name": "test_tool", "args": {"message": "hello world"}}\n',
        "§execute\n",
        "§respond: The tool completed successfully.\n",
        "§end\n",
    ]

    llm = mock_llm.set_response_tokens(protocol_tokens)
    agent = Agent(llm=llm, tools=[mock_tool()], mode="replay", max_iterations=1)
    events = [event async for event in agent("Test query", chunks=False)]

    assert len(events) >= 5
    assert events[0]["type"] == "user"
    assert events[0]["content"] == "Test query"
    assert events[1]["type"] == "think"
    assert "need to call a tool" in events[1]["content"]
    assert events[2]["type"] == "call"
    assert events[3]["type"] == "execute"
    assert events[4]["type"] == "metric"
    assert events[5]["type"] == "result"
    assert "Tool executed: hello world" in events[5]["payload"]["outcome"]


@pytest.mark.asyncio
async def test_chunks(mock_llm, mock_tool):
    protocol_tokens = [
        "§think: Think",
        "ing...\n",
        '§call: {"name": "test_tool", "args": {"message": "test"}}\n',
        "§execute\n",
        "§respond: Done!\n",
        "§end\n",
    ]

    llm = mock_llm.set_response_tokens(protocol_tokens)
    agent = Agent(llm=llm, tools=[mock_tool()], mode="replay", max_iterations=1)
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
    agent = Agent(llm=llm, tools=[mock_tool()], mode="replay", max_iterations=1)
    events = [event async for event in agent("Test query", chunks=False)]

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
    failing_tool = mock_tool().configure(
        name="failing_tool", description="Tool that fails", should_fail=True
    )
    agent = Agent(llm=llm, tools=[failing_tool], mode="replay", max_iterations=1)

    with pytest.raises(AgentError, match=r"Tool execution failed"):
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
    agent = Agent(
        llm=llm, tools=[mock_tool()], storage=mock_storage, mode="replay", max_iterations=1
    )
    events = [event async for event in agent("Test query", chunks=False)]

    assert len(events) >= 3
    assert any(e["type"] == "user" for e in events)
    assert any(e["type"] == "think" for e in events)
    assert any(e["type"] == "result" for e in events)


@pytest.mark.asyncio
async def test_event_taxonomy(mock_llm, mock_tool):
    """Verify complete event taxonomy with multi-iteration flow.
    
    With parser hardstop on §execute, respond/end come in iteration 2.
    This tests the full nominal path:
    - Iter 1: think → call tool → execute (hardstop)
    - Tool executes with result
    - Iter 2: (with tool result in context) → respond → end
    """
    iteration_tokens = [
        [
            "§think: reasoning\n",
            '§call: {"name": "test_tool", "args": {"message": "test"}}\n',
            "§execute\n",
        ],
        [
            "§respond: result processed\n",
            "§end\n",
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
    
    agent = Agent(llm=MultiIterMockLLM(), tools=[mock_tool()], mode="replay", max_iterations=2)
    events = [event async for event in agent("Test", chunks=False)]

    event_types = [e["type"] for e in events]

    # Verify all core events present
    assert "user" in event_types
    assert "think" in event_types
    assert "call" in event_types
    assert "execute" in event_types
    assert "result" in event_types
    assert "respond" in event_types
    assert "end" in event_types
    assert "metric" in event_types

    # Verify order within iteration sequences
    user_idx = event_types.index("user")
    think_idx = event_types.index("think")
    call_idx = event_types.index("call")
    execute_idx = event_types.index("execute")
    result_idx = event_types.index("result")
    respond_idx = event_types.index("respond")
    end_idx = event_types.index("end")

    # Iteration 1 sequence: user → think → call → execute → result
    assert user_idx < think_idx < call_idx < execute_idx < result_idx
    # Iteration 2 sequence: respond comes after, then end
    assert result_idx < respond_idx < end_idx


@pytest.mark.asyncio
async def test_generate_mode(mock_llm, mock_tool):
    """Parser accepts complete string from LLM.generate()."""

    completion = "§think: analyzing request §respond: The answer is 42 §end"

    class GenerateMockLLM:
        async def generate(self, messages):
            return completion

        async def stream(self, messages):
            for token in completion:
                yield token

    agent = Agent(llm=GenerateMockLLM(), tools=[mock_tool()], mode="replay", max_iterations=1)
    events = [event async for event in agent("Test", chunks=False, generate=True)]

    event_types = [e["type"] for e in events]

    assert "user" in event_types
    assert "think" in event_types
    assert "respond" in event_types
    assert "end" in event_types

    think_event = next(e for e in events if e["type"] == "think")
    assert "analyzing request" in think_event["content"]

    respond_event = next(e for e in events if e["type"] == "respond")
    assert "42" in respond_event["content"]
