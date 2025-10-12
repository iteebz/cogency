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
async def test_user_with_think_respond():
    events = [
        {"type": "user", "content": "debug this"},
        {"type": "think", "content": "need to check logs"},
        {"type": "respond", "content": "found the issue"},
    ]
    messages = conversation.to_messages(events)

    assert len(messages) == 2
    assert messages[0] == {"role": "user", "content": "debug this"}
    assert messages[1] == {
        "role": "assistant",
        "content": "§think: need to check logs\n§respond: found the issue",
    }


@pytest.mark.asyncio
async def test_call_execute_result_turn_boundary():
    events = [
        {"type": "user", "content": "read app.py"},
        {"type": "think", "content": "reading file"},
        {"type": "call", "content": '{"name": "file_read", "args": {"path": "app.py"}}'},
        {"type": "result", "content": '{"outcome": "Success", "content": "def main(): pass"}'},
        {"type": "respond", "content": "here is the code"},
    ]
    messages = conversation.to_messages(events)

    assert len(messages) == 4
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    assert "§execute" in messages[1]["content"]
    assert messages[2]["role"] == "user"
    assert messages[3]["role"] == "assistant"


@pytest.mark.asyncio
async def test_execute_synthesized_at_call_result_boundary():
    events = [
        {"type": "user", "content": "test"},
        {"type": "call", "content": '{"name": "tool", "args": {}}'},
        {"type": "result", "content": '{"outcome": "Success", "content": "done"}'},
    ]
    messages = conversation.to_messages(events)

    assistant_msg = messages[1]
    assert "§execute" in assistant_msg["content"]
    assert assistant_msg["content"].endswith("§execute")


@pytest.mark.asyncio
async def test_no_execute_when_call_not_followed_by_result():
    events = [
        {"type": "user", "content": "test"},
        {"type": "call", "content": '{"name": "tool", "args": {}}'},
    ]
    messages = conversation.to_messages(events)

    assistant_msg = messages[1]
    assert "§execute" not in assistant_msg["content"]


@pytest.mark.asyncio
async def test_multiple_turns():
    events = [
        {"type": "user", "content": "hi"},
        {"type": "respond", "content": "hello"},
        {"type": "user", "content": "bye"},
        {"type": "respond", "content": "goodbye"},
    ]
    messages = conversation.to_messages(events)

    assert len(messages) == 4
    assert messages[0] == {"role": "user", "content": "hi"}
    assert messages[1] == {"role": "assistant", "content": "§respond: hello"}
    assert messages[2] == {"role": "user", "content": "bye"}
    assert messages[3] == {"role": "assistant", "content": "§respond: goodbye"}


@pytest.mark.asyncio
async def test_result_formatting():
    events = [
        {"type": "user", "content": "test"},
        {"type": "call", "content": '{"name": "tool", "args": {}}'},
        {"type": "result", "content": '{"outcome": "Success", "content": "output here"}'},
    ]
    messages = conversation.to_messages(events)

    result_msg = messages[2]
    assert result_msg["role"] == "user"
    assert "Success" in result_msg["content"]


@pytest.mark.asyncio
async def test_delimiters_synthesized_not_stored():
    events = [
        {"type": "user", "content": "test"},
        {"type": "think", "content": "analyzing"},
        {"type": "respond", "content": "done"},
    ]
    messages = conversation.to_messages(events)

    assert messages[0]["content"] == "test"
    assert messages[1]["content"] == "§think: analyzing\n§respond: done"


@pytest.mark.asyncio
async def test_complex_conversation_flow():
    events = [
        {"type": "user", "content": "debug app.py"},
        {"type": "think", "content": "should read file first"},
        {"type": "call", "content": '{"name": "file_read", "args": {"path": "app.py"}}'},
        {"type": "result", "content": '{"outcome": "Success", "content": "code..."}'},
        {"type": "think", "content": "found the bug"},
        {
            "type": "call",
            "content": '{"name": "file_write", "args": {"path": "app.py", "content": "fixed..."}}',
        },
        {"type": "result", "content": '{"outcome": "Success", "content": "written"}'},
        {"type": "respond", "content": "fixed the bug"},
    ]
    messages = conversation.to_messages(events)

    assert len(messages) == 6
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    assert "§execute" in messages[1]["content"]
    assert messages[2]["role"] == "user"
    assert messages[3]["role"] == "assistant"
    assert "§execute" in messages[3]["content"]
    assert messages[4]["role"] == "user"
    assert messages[5]["role"] == "assistant"
