import pytest

from cogency.core.parser import parse_tokens


async def mock_token_stream(tokens):
    for token in tokens:
        yield token


@pytest.mark.asyncio
async def test_basic_protocol():
    tokens = ["Hello", " §think:", " analyzing", " §respond:", " done"]

    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    assert len(events) == 5
    assert events[0] == {"type": "respond", "content": "Hello"}
    assert events[1] == {"type": "respond", "content": " "}
    assert events[2] == {"type": "think", "content": " analyzing"}
    assert events[3] == {"type": "think", "content": " "}
    assert events[4] == {"type": "respond", "content": " done"}


@pytest.mark.asyncio
async def test_split_delimiter_across_tokens():
    # Gemini splits: '§think' + ': content'
    tokens = ["§think", ": The user is asking to read 'test.txt'", " §end"]

    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    assert len(events) == 3
    assert events[0]["type"] == "think"
    assert events[0]["content"] == "The user is asking to read 'test.txt'"
    assert events[1] == {"type": "think", "content": " "}
    assert events[2]["type"] == "end"


@pytest.mark.asyncio
async def test_end_delimiter_terminates():
    tokens = ["Done", " with", " task", " §end:", " ignored", " content"]

    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    assert len(events) == 5
    assert events[0]["content"] == "Done"
    assert events[1]["content"] == " with"
    assert events[2]["content"] == " task"
    assert events[3]["content"] == " "
    assert events[4]["type"] == "end"


@pytest.mark.asyncio
async def test_malformed_delimiters():
    tokens = ["§invalid:", " §", " BROKEN:", " §think", " without", " colon"]

    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    assert len(events) == 6
    assert events[0]["content"] == "§invalid:"
    assert events[1]["content"] == " "
    assert events[2]["content"] == "§ BROKEN:"
    assert events[3]["content"] == " "
    assert events[4]["content"] == "§think without"
    assert events[5]["content"] == " colon"


@pytest.mark.asyncio
async def test_non_string_tokens_error():
    async def bad_token_stream():
        yield "valid"
        yield 123
        yield "more"

    with pytest.raises(RuntimeError, match="Parser expects string tokens"):
        async for _event in parse_tokens(bad_token_stream()):
            pass


@pytest.mark.asyncio
async def test_massive_word_buffer():
    giant_word = "x" * 10000
    tokens = [giant_word, " normal"]

    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    assert len(events) == 2
    assert events[0]["content"] == giant_word
    assert events[1]["content"] == " normal"


@pytest.mark.asyncio
async def test_delimiter_boundary_splitting():
    tokens = ["§thi", "NK:", " content"]

    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    assert len(events) == 1
    assert events[0]["type"] == "think"
    assert events[0]["content"] == " content"


@pytest.mark.asyncio
async def test_multi_token_delimiter():
    tokens = ["§", "respond", ":", " The", " answer", " §", "end"]

    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    assert len(events) == 4
    assert events[0] == {"type": "respond", "content": " The"}
    assert events[1] == {"type": "respond", "content": " answer"}
    assert events[2] == {"type": "respond", "content": " "}
    assert events[3] == {"type": "end"}


@pytest.mark.asyncio
async def test_single_token_delimiter():
    tokens = ["§think: analyzing", " §execute", " §end"]

    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    assert len(events) == 5
    assert events[0] == {"type": "think", "content": "analyzing"}
    assert events[1] == {"type": "think", "content": " "}
    assert events[2] == {"type": "execute"}
    assert events[3] == {"type": "respond", "content": " "}
    assert events[4] == {"type": "end"}


@pytest.mark.asyncio
async def test_embedded_delimiter():
    tokens = ["§respond: The answer is 8\n§end"]

    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    assert len(events) == 2
    assert events[0] == {"type": "respond", "content": "The answer is 8\n"}
    assert events[1] == {"type": "end"}


@pytest.mark.asyncio
async def test_embedded_delimiter_simple():
    tokens = ["8\n§end"]

    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)
    assert len(events) == 2
    assert events[0] == {"type": "respond", "content": "8\n"}
    assert events[1] == {"type": "end"}


@pytest.mark.asyncio
async def test_split_delimiter_boundary():
    tokens = [
        "§respond: I will read the content of test.txt for you.\n§",
        "think: To read the content, I should use the file_read tool.",
    ]

    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    assert len(events) == 2
    assert events[0]["type"] == "respond"
    assert "I will read the content" in events[0]["content"]
    assert events[1]["type"] == "think"
    assert "To read the content" in events[1]["content"]


@pytest.mark.asyncio
async def test_multiple_embedded_delimiters():
    tokens = [
        "§respond: I will read the content of test.txt for you.\n§",
        'think: To read the content, I should use the file_read tool.\n§call: {"name": "file_read", "args": {"file": "test.txt"}}\n§execute',
    ]

    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    assert len(events) == 4
    assert events[0]["type"] == "respond"
    assert "I will read the content" in events[0]["content"]
    assert events[1]["type"] == "think"
    assert "To read the content" in events[1]["content"]
    assert events[2]["type"] == "call"
    assert "file_read" in events[2]["content"]
    assert events[3]["type"] == "execute"


@pytest.mark.asyncio
async def test_whitespace_preservation():
    """Parser preserves whitespace faithfully, no accumulation bug."""
    tokens = ["hello", " ", "world", " §execute"]

    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    assert len(events) == 5
    assert events[0]["content"] == "hello"
    assert events[1]["content"] == " "
    assert events[2]["content"] == "world"
    assert events[3]["content"] == " "
    assert events[4]["type"] == "execute"


@pytest.mark.asyncio
async def test_eager_emit_no_delimiters():
    """Tokens without delimiters stream immediately."""
    tokens = ["Hello", " world", "!"]

    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    assert len(events) == 3
    assert events[0] == {"type": "respond", "content": "Hello"}
    assert events[1] == {"type": "respond", "content": " world"}
    assert events[2] == {"type": "respond", "content": "!"}


@pytest.mark.asyncio
async def test_eager_emit_partial_delimiter_held():
    """Partial delimiter candidates are held until resolved."""
    tokens = ["Hello §", "think", ": analyzing"]

    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    assert len(events) == 2
    assert events[0] == {"type": "respond", "content": "Hello "}
    assert events[1] == {"type": "think", "content": "analyzing"}


@pytest.mark.asyncio
async def test_eager_emit_false_alarm_delimiter():
    """False alarm partial delimiter held until resolved."""
    tokens = ["Price: §", "50"]

    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    assert len(events) == 2
    assert events[0] == {"type": "respond", "content": "Price: "}
    assert events[1] == {"type": "respond", "content": "§50"}
