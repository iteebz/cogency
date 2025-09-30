import json

import pytest

from cogency.core.exceptions import ProtocolError
from cogency.tools.parse import _auto_escape_content, parse_tool_call, parse_tool_result


def test_unescaped_quotes():
    malformed_json_str = (
        '{"name": "file_write", "args": {"file": "app.py", "content": "print(\\"hello world\\")"}}'
    )

    tool_call = parse_tool_call(malformed_json_str)

    assert tool_call.name == "file_write"
    assert tool_call.args["file"] == "app.py"
    assert tool_call.args["content"] == 'print("hello world")'


def test_newlines():
    malformed_json_str = (
        '{"name": "file_write", "args": {"file": "test.txt", "content": "line1\nline2\nline3"}}'
    )

    tool_call = parse_tool_call(malformed_json_str)

    assert tool_call.name == "file_write"
    assert tool_call.args["file"] == "test.txt"
    assert tool_call.args["content"] == "line1\nline2\nline3"


def test_extra_data():
    # Extra data at the end
    malformed_json_str_end = '{"name": "tool", "args": {"key": "value"}}§execute§execute'
    tool_call_end = parse_tool_call(malformed_json_str_end)
    assert tool_call_end.name == "tool"
    assert tool_call_end.args["key"] == "value"

    # Extra data at the beginning
    malformed_json_str_start = (
        'Thought: I need to call a tool.{"name": "tool", "args": {"key": "value"}}'
    )
    tool_call_start = parse_tool_call(malformed_json_str_start)
    assert tool_call_start.name == "tool"
    assert tool_call_start.args["key"] == "value"

    # Extra data at both ends
    malformed_json_str_both = 'Thought: {"name": "tool", "args": {"key": "value"}}§execute'
    tool_call_both = parse_tool_call(malformed_json_str_both)
    assert tool_call_both.name == "tool"
    assert tool_call_both.args["key"] == "value"


def test_unquoted_keys():
    malformed_json_str = '{"name": "tool", args: {"key": "value"}}'
    tool_call = parse_tool_call(malformed_json_str)
    assert tool_call.name == "tool"
    assert tool_call.args["key"] == "value"

    malformed_json_str_nested = '{"name": "tool", "args": {key: "value", anotherKey: 123}}'
    tool_call_nested = parse_tool_call(malformed_json_str_nested)
    assert tool_call_nested.name == "tool"
    assert tool_call_nested.args["key"] == "value"
    assert tool_call_nested.args["anotherKey"] == 123


def test_result_formats():
    # New format (payload dictionary - though parse_tool_result expects content string)
    new_format_content = json.dumps({"outcome": "Success", "content": "New format output"})
    results = parse_tool_result(new_format_content)
    assert len(results) == 1
    assert results[0].outcome == "Success"
    assert results[0].content == "New format output"

    # Old format (JSON array of dictionaries)
    old_array_content = json.dumps(
        [{"outcome": "Old Array Success", "content": "Old array output"}]
    )
    results = parse_tool_result(old_array_content)
    assert len(results) == 1
    assert results[0].outcome == "Old Array Success"
    assert results[0].content == "Old array output"

    # Old format (JSON object dictionary - single result)
    old_object_content = json.dumps(
        {"outcome": "Old Object Success", "content": "Old object output"}
    )
    results = parse_tool_result(old_object_content)
    assert len(results) == 1
    assert results[0].outcome == "Old Object Success"
    assert results[0].content == "Old object output"

    # Simple string (fallback)
    simple_string_content = "Just a plain string result"
    results = parse_tool_result(simple_string_content)
    assert len(results) == 1
    assert results[0].outcome == "Just a plain string result"
    assert results[0].content == ""

    # Malformed JSON string
    malformed_json_content = "{not valid json}"
    results = parse_tool_result(malformed_json_content)
    assert len(results) == 1
    assert results[0].outcome == "{not valid json}"
    assert results[0].content == ""


def test_missing_colon():
    # Missing colon after quoted key (simple case)
    malformed_json = '{"name": "file_write", "args" {"file": "test.py"}}'
    tool_call = parse_tool_call(malformed_json)
    assert tool_call.name == "file_write"
    assert tool_call.args["file"] == "test.py"


def test_simple_cases():
    # Valid JSON works
    valid_json = '{"name": "file_write", "args": {"content": "simple text"}}'
    tool_call = parse_tool_call(valid_json)
    assert tool_call.name == "file_write"
    assert tool_call.args["content"] == "simple text"


def test_auto_escape_newlines_quotes():
    unescaped_json = '{"name": "file_write", "args": {"file": "test.py", "content": "def foo():\n    return "hello""}}'
    escaped_json = _auto_escape_content(unescaped_json)
    expected = '{"name": "file_write", "args": {"file": "test.py", "content": "def foo():\\n    return \\"hello\\""}}'
    assert escaped_json == expected

    tool_call = parse_tool_call(unescaped_json)
    assert tool_call.name == "file_write"
    assert tool_call.args["content"] == 'def foo():\n    return "hello"'


def test_escape_content_only():
    json_with_quotes = (
        '{"name": "test_tool", "args": {"file": "has"quotes.py", "content": "print("hi")"}}'
    )
    escaped = _auto_escape_content(json_with_quotes)
    expected = (
        '{"name": "test_tool", "args": {"file": "has"quotes.py", "content": "print(\\"hi\\")"}}'
    )
    assert escaped == expected


def test_auto_escape_backslashes():
    json_str = '{"name": "file_write", "args": {"content": "path\\to\\file"}}'
    escaped = _auto_escape_content(json_str)
    expected = '{"name": "file_write", "args": {"content": "path\\\\to\\\\file"}}'
    assert escaped == expected


def test_auto_escape_integration():
    # This was the failing case from the original bug report
    malformed_json = '{"name": "file_write", "args": {"file": "models.py", "content": "user = db.relationship(\'User\', backref=db.backref(\'comments\', lazy=True))"}}'

    # Should parse successfully with auto-escape
    tool_call = parse_tool_call(malformed_json)
    assert tool_call.name == "file_write"
    assert tool_call.args["file"] == "models.py"
    assert "user = db.relationship('User'" in tool_call.args["content"]


def test_concatenated_json():
    concatenated_json = '{"name": "file_write", "args": {"file": "first.txt"}} {"name": "shell", "args": {"command": "echo second"}}'
    tool_call = parse_tool_call(concatenated_json)
    assert tool_call.name == "file_write"
    assert tool_call.args["file"] == "first.txt"


def test_complex_fails():
    complex_content = """{
        "name": "file_write",
        "args": {
            "file": "models.py",
            "content": "class User(db.Model):\n    name = db.Column(db.String(80))\n    def __repr__(self):\n        return f'<User {self.name}>'"
        }
    }"""
    with pytest.raises(ProtocolError):
        parse_tool_call(complex_content)
