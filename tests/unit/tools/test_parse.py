import pytest

from cogency.core.exceptions import ProtocolError
from cogency.tools.parse import _auto_escape_content, parse_tool_call, parse_tool_result


def test_valid_json():
    result = parse_tool_call('{"name": "write", "args": {"file": "test.txt"}}')
    assert result.name == "write"
    assert result.args["file"] == "test.txt"


def test_extra_data():
    result = parse_tool_call('prefix{"name": "tool", "args": {}}suffix')
    assert result.name == "tool"


def test_unquoted_keys():
    with pytest.raises(ProtocolError):
        parse_tool_call('{"name": "tool", args: {key: "val"}}')


def test_missing_colon():
    with pytest.raises(ProtocolError):
        parse_tool_call('{"name": "tool", "args" {"key": "val"}}')


def test_auto_escape_content():
    escaped = _auto_escape_content('{"name": "w", "args": {"content": "a\nb"}}')
    assert escaped == '{"name": "w", "args": {"content": "a\\nb"}}'


def test_auto_escape_quotes():
    json_str = '{"name": "w", "args": {"content": "say "hi""}}'
    result = parse_tool_call(json_str)
    assert result.args["content"] == 'say "hi"'


def test_auto_escape_backslashes():
    json_str = '{"name": "w", "args": {"content": "path\\to\\file"}}'
    result = parse_tool_call(json_str)
    assert result.args["content"] == "path\to\file"


def test_complex_fails():
    with pytest.raises(ProtocolError):
        parse_tool_call('{"name": "w", "args": {"c": "unclosed string}}')


def test_result_dict():
    results = parse_tool_result('{"outcome": "ok", "content": "data"}')
    assert len(results) == 1
    assert results[0].outcome == "ok"
    assert results[0].content == "data"


def test_result_list():
    results = parse_tool_result('[{"outcome": "ok", "content": "data"}]')
    assert len(results) == 1
    assert results[0].outcome == "ok"


def test_result_string_fallback():
    results = parse_tool_result("plain text")
    assert len(results) == 1
    assert results[0].outcome == "plain text"
    assert results[0].content == ""


def test_result_malformed_json():
    results = parse_tool_result("{bad json}")
    assert len(results) == 1
    assert results[0].outcome == "{bad json}"
