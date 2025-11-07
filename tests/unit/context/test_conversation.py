import json

import pytest

from cogency.context import conversation


@pytest.mark.asyncio
async def test_empty_events():
    messages = conversation.to_messages([])
    assert messages == []


@pytest.mark.asyncio
async def test_single_user_message():
    events = [{"type": "user", "content": "hello"}]
    messages = conversation.to_messages(events)

    assert len(messages) == 1
    assert messages[0] == {"role": "user", "content": "hello"}


@pytest.mark.asyncio
async def test_user_think_respond():
    events = [
        {"type": "user", "content": "debug this"},
        {"type": "think", "content": "need to check logs"},
        {"type": "respond", "content": "found the issue"},
    ]
    messages = conversation.to_messages(events)

    assert len(messages) == 2
    assert messages[0] == {"role": "user", "content": "debug this"}
    assert messages[1]["role"] == "assistant"
    assert "<think>need to check logs</think>" in messages[1]["content"]
    assert "found the issue" in messages[1]["content"]


@pytest.mark.asyncio
async def test_single_call_reconstruct_to_json_array():
    """Single call reconstructs to JSON array in execute block."""
    events = [
        {"type": "user", "content": "read app.py"},
        {"type": "call", "content": '{"name": "read", "args": {"file": "app.py"}}'},
        {"type": "result", "content": '{"outcome": "Success", "content": "def main(): pass"}'},
    ]
    messages = conversation.to_messages(events)

    assert len(messages) == 3
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    assert "<execute>" in messages[1]["content"]
    assert "</execute>" in messages[1]["content"]

    execute_block = messages[1]["content"]
    start = execute_block.find("[")
    end = execute_block.rfind("]") + 1
    json_array = json.loads(execute_block[start:end])
    assert isinstance(json_array, list)
    assert json_array[0]["name"] == "read"
    assert json_array[0]["args"]["file"] == "app.py"


@pytest.mark.asyncio
async def test_multiple_calls_reconstruct_batched():
    """Multiple calls reconstructed as single JSON array batch."""
    events = [
        {"type": "user", "content": "batch read"},
        {"type": "call", "content": '{"name": "read", "args": {"file": "a.txt"}}'},
        {"type": "call", "content": '{"name": "read", "args": {"file": "b.txt"}}'},
        {"type": "call", "content": '{"name": "write", "args": {"file": "c.txt", "content": "x"}}'},
        {
            "type": "result",
            "content": '[{"tool": "read", "status": "success"}, {"tool": "read", "status": "success"}, {"tool": "write", "status": "success"}]',
        },
    ]
    messages = conversation.to_messages(events)

    assert len(messages) == 3
    assistant_msg = messages[1]
    assert "<execute>" in assistant_msg["content"]

    execute_block = assistant_msg["content"]
    start = execute_block.find("[")
    end = execute_block.rfind("]") + 1
    json_array = json.loads(execute_block[start:end])
    assert len(json_array) == 3
    assert json_array[0]["name"] == "read"
    assert json_array[1]["name"] == "read"
    assert json_array[2]["name"] == "write"
    assert json_array[0]["args"]["file"] == "a.txt"
    assert json_array[1]["args"]["file"] == "b.txt"
    assert json_array[2]["args"]["content"] == "x"


@pytest.mark.asyncio
async def test_call_order_preserved_in_reconstruction():
    """Call order preserved in reconstructed JSON array."""
    events = [
        {"type": "user", "content": "test"},
        {"type": "call", "content": '{"name": "read", "args": {"file": "1.txt"}}'},
        {"type": "call", "content": '{"name": "read", "args": {"file": "2.txt"}}'},
        {"type": "call", "content": '{"name": "read", "args": {"file": "3.txt"}}'},
        {"type": "result", "content": "[]"},
    ]
    messages = conversation.to_messages(events)

    assistant_msg = messages[1]
    execute_block = assistant_msg["content"]
    start = execute_block.find("[")
    end = execute_block.rfind("]") + 1
    json_array = json.loads(execute_block[start:end])

    assert json_array[0]["args"]["file"] == "1.txt"
    assert json_array[1]["args"]["file"] == "2.txt"
    assert json_array[2]["args"]["file"] == "3.txt"


@pytest.mark.asyncio
async def test_no_calls_before_result():
    """Result without preceding calls doesn't create execute block."""
    events = [
        {"type": "user", "content": "test"},
        {"type": "respond", "content": "thinking..."},
        {"type": "result", "content": "[]"},
    ]
    messages = conversation.to_messages(events)

    assert len(messages) == 3
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "test"
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "[]"
    assert messages[2]["role"] == "assistant"
    assert "thinking..." in messages[2]["content"]
    assert "<execute>" not in messages[2]["content"]


@pytest.mark.asyncio
async def test_multiple_batches_separate_execute_blocks():
    """Multiple call batches create separate execute blocks."""
    events = [
        {"type": "user", "content": "test"},
        {"type": "call", "content": '{"name": "read", "args": {"file": "a.txt"}}'},
        {"type": "result", "content": "[]"},
        {"type": "call", "content": '{"name": "write", "args": {"file": "b.txt", "content": "x"}}'},
        {"type": "result", "content": "[]"},
    ]
    messages = conversation.to_messages(events)

    execute_blocks = [m for m in messages if "<execute>" in m.get("content", "")]
    assert len(execute_blocks) == 2


@pytest.mark.asyncio
async def test_collision_html_content_preserved():
    """HTML content in args preserved correctly in reconstruction."""
    html_content = "<html><body>Hello</body></html>"
    events = [
        {"type": "user", "content": "test"},
        {
            "type": "call",
            "content": f'{{"name": "write", "args": {{"file": "index.html", "content": "{html_content}"}}}}',
        },
        {"type": "result", "content": "[]"},
    ]
    messages = conversation.to_messages(events)

    assistant_msg = messages[1]
    assert html_content in assistant_msg["content"]


@pytest.mark.asyncio
async def test_collision_closing_tag_in_args():
    """Closing tag in args (</write>) preserved in reconstruction."""
    events = [
        {"type": "user", "content": "test"},
        {
            "type": "call",
            "content": '{"name": "write", "args": {"content": "Hello </write> world"}}',
        },
        {"type": "result", "content": "[]"},
    ]
    messages = conversation.to_messages(events)

    assistant_msg = messages[1]
    assert "</write>" in assistant_msg["content"]


@pytest.mark.asyncio
async def test_roundtrip_single_tool():
    """Roundtrip: parse → reconstruct → parse again (single tool)."""
    original_call = {"name": "read", "args": {"file": "test.txt"}}
    events = [
        {"type": "user", "content": "test"},
        {"type": "call", "content": json.dumps(original_call)},
        {"type": "result", "content": "[]"},
    ]

    messages = conversation.to_messages(events)
    assistant_msg = messages[1]["content"]

    start = assistant_msg.find("[")
    end = assistant_msg.rfind("]") + 1
    reconstructed_array = json.loads(assistant_msg[start:end])

    assert reconstructed_array[0] == original_call


@pytest.mark.asyncio
async def test_roundtrip_multiple_tools():
    """Roundtrip: parse → reconstruct → parse again (multiple tools)."""
    calls = [
        {"name": "read", "args": {"file": "a.txt"}},
        {"name": "write", "args": {"file": "b.txt", "content": "data"}},
        {"name": "read", "args": {"file": "c.txt"}},
    ]
    events = [
        {"type": "user", "content": "test"},
    ]
    for call in calls:
        events.append({"type": "call", "content": json.dumps(call)})
    events.append({"type": "result", "content": "[]"})

    messages = conversation.to_messages(events)
    assistant_msg = messages[1]["content"]

    start = assistant_msg.find("[")
    end = assistant_msg.rfind("]") + 1
    reconstructed_array = json.loads(assistant_msg[start:end])

    assert len(reconstructed_array) == 3
    for i, original_call in enumerate(calls):
        assert reconstructed_array[i] == original_call


@pytest.mark.asyncio
async def test_result_formatting_injected():
    """Results injected as user message after execute block."""
    events = [
        {"type": "user", "content": "test"},
        {"type": "call", "content": '{"name": "read", "args": {"file": "test.txt"}}'},
        {"type": "result", "content": '{"outcome": "Success", "content": "output"}'},
    ]
    messages = conversation.to_messages(events)

    assert len(messages) == 3
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    assert messages[2]["role"] == "user"
    assert "Success" in messages[2]["content"]


@pytest.mark.asyncio
async def test_complex_flow_two_batches():
    """Complex flow with two separate call batches."""
    events = [
        {"type": "user", "content": "debug app.py"},
        {"type": "think", "content": "should read file first"},
        {"type": "call", "content": '{"name": "read", "args": {"file": "app.py"}}'},
        {"type": "result", "content": '{"outcome": "Success", "content": "code..."}'},
        {"type": "think", "content": "found the bug"},
        {
            "type": "call",
            "content": '{"name": "write", "args": {"file": "app.py", "content": "fixed..."}}',
        },
        {"type": "result", "content": '{"outcome": "Success", "content": "written"}'},
        {"type": "respond", "content": "fixed the bug"},
    ]
    messages = conversation.to_messages(events)

    assert len(messages) == 6
    assert messages[0]["role"] == "user"

    assert messages[1]["role"] == "assistant"
    assert "<think>" in messages[1]["content"]
    assert "<execute>" in messages[1]["content"]

    assert messages[2]["role"] == "user"

    assert messages[3]["role"] == "assistant"
    assert "<think>" in messages[3]["content"]
    assert "<execute>" in messages[3]["content"]

    assert messages[4]["role"] == "user"

    assert messages[5]["role"] == "assistant"
    assert "fixed the bug" in messages[5]["content"]
