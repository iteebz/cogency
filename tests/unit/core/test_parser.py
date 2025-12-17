"""Unit tests for Cogency XML protocol parser.

Tests the XML-based protocol parser. Contract: accept token stream
(or complete string) and emit standardized events for accumulator.
"""

import json

import pytest

from cogency.core.parser import parse_tokens


async def mock_token_stream(tokens):
    """Helper to wrap tokens in async generator."""
    for token in tokens:
        yield token


@pytest.mark.asyncio
async def test_think_block_simple():
    """Parse simple think block."""
    xml = "<think>reasoning here</think>"
    events = []
    async for event in parse_tokens(xml):
        events.append(event)

    assert len(events) == 1
    assert events[0]["type"] == "think"
    assert events[0]["content"] == "reasoning here"


@pytest.mark.asyncio
async def test_execute_single_tool_json_array():
    """Parse execute block with single tool in JSON array format."""
    xml = """<execute>
[
  {"name": "read", "args": {"file": "test.txt"}}
]
</execute>"""
    events = []
    async for event in parse_tokens(xml):
        events.append(event)

    assert len(events) == 2
    assert events[0]["type"] == "call"
    assert events[1]["type"] == "execute"

    call_data = json.loads(events[0]["content"])
    assert call_data["name"] == "read"
    assert call_data["args"]["file"] == "test.txt"


@pytest.mark.asyncio
async def test_execute_multiple_tools_json_array():
    """Parse execute block with multiple tools - order preserved."""
    xml = """<execute>
[
  {"name": "read", "args": {"file": "a.txt"}},
  {"name": "write", "args": {"file": "b.txt", "content": "x"}}
]
</execute>"""
    events = []
    async for event in parse_tokens(xml):
        events.append(event)

    assert len(events) == 3
    assert events[0]["type"] == "call"
    assert events[1]["type"] == "call"
    assert events[2]["type"] == "execute"

    call1 = json.loads(events[0]["content"])
    call2 = json.loads(events[1]["content"])
    assert call1["name"] == "read"
    assert call2["name"] == "write"


@pytest.mark.parametrize(
    "content,field",
    [
        ("<html><body>Hello </body></html>", "content"),
        ("Hello </write> world", "content"),
        ("<root><child>value</child></root>", "content"),
    ],
)
@pytest.mark.asyncio
async def test_collision_content_safe(content, field):
    """XML collision: Unsafe content safely escaped in JSON."""
    xml = f"""<execute>
[
  {{"name": "write", "args": {{"{field}": {json.dumps(content)}}}}}
]
</execute>"""
    events = []
    async for event in parse_tokens(xml):
        events.append(event)

    assert len(events) == 2
    assert events[0]["type"] == "call"
    call_data = json.loads(events[0]["content"])
    assert call_data["args"][field] == content


@pytest.mark.asyncio
async def test_results_block():
    """Parse results block with JSON array."""
    xml = """<results>
[
  {"tool": "read", "status": "success", "content": "data"},
  {"tool": "write", "status": "success", "content": {"bytes": 10}}
]
</results>"""
    events = []
    async for event in parse_tokens(xml):
        events.append(event)

    assert len(events) == 1
    assert events[0]["type"] == "result"

    results = json.loads(events[0]["content"])
    assert len(results) == 2
    assert results[0]["tool"] == "read"


@pytest.mark.asyncio
async def test_full_sequence_think_execute():
    """Parse think + execute sequence — parser stops after execute.

    Results are system-injected in a new iteration, not parsed from same stream.
    """
    xml = """<think>reading config and updating endpoint</think>
<execute>
[
  {"name": "read", "args": {"file": "config.json"}}
]
</execute>"""
    events = []
    async for event in parse_tokens(xml):
        events.append(event)

    types = [e["type"] for e in events]
    assert types == ["think", "call", "execute"]


@pytest.mark.asyncio
async def test_streaming_tokens_split_across_tokens():
    """Handle tag split across tokens."""
    tokens = ["<thi", "nk>reasoning</t", "hink>"]
    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    assert len(events) == 1
    assert events[0]["type"] == "think"
    assert events[0]["content"] == "reasoning"


@pytest.mark.asyncio
async def test_tag_split_character_by_character():
    """Tag split character-by-character across tokens."""
    xml = "<think>hello</think>"
    tokens = list(xml)
    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    assert len(events) == 1
    assert events[0]["type"] == "think"
    assert events[0]["content"] == "hello"


@pytest.mark.asyncio
async def test_partial_closing_tag_held():
    """Partial closing tag held until complete."""
    tokens = ["<think>content</thi", "nk>after"]
    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    types = [e["type"] for e in events]
    assert "think" in types
    assert "respond" in types


@pytest.mark.asyncio
async def test_multiple_tags_same_token_ordered():
    """Multiple tags in single token processed in order."""
    xml = "<think>first</think><think>second</think>"
    events = []
    async for event in parse_tokens(xml):
        events.append(event)

    thinks = [e for e in events if e["type"] == "think"]
    assert len(thinks) == 2
    assert thinks[0]["content"] == "first"
    assert thinks[1]["content"] == "second"


@pytest.mark.asyncio
async def test_mixed_tags_streaming_tokens():
    """Mixed tags across streaming tokens preserve order until execute.

    Parser terminates after execute — results come from system in next iteration.
    """
    tokens = [
        "<think>reasoning</think>",
        '<execute>[{"name": "read", "args": {"file": "test.txt"}}]</execute>',
    ]
    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    types = [e["type"] for e in events]
    assert types == ["think", "call", "execute"]


@pytest.mark.asyncio
async def test_execute_order_preserved_multiple_tools():
    """Multiple tools in execute block produce calls in order."""
    xml = """<execute>
[
  {"name": "read", "args": {"file": "1.txt"}},
  {"name": "write", "args": {"file": "2.txt", "content": "x"}},
  {"name": "read", "args": {"file": "3.txt"}}
]
</execute>"""
    events = []
    async for event in parse_tokens(xml):
        events.append(event)

    calls = [e for e in events if e["type"] == "call"]
    files = [json.loads(c["content"])["args"]["file"] for c in calls]
    assert files == ["1.txt", "2.txt", "3.txt"]


@pytest.mark.asyncio
async def test_results_order_matches_execution():
    """Results array order preserved from execution."""
    xml = """<results>
[
  {"tool": "read", "status": "success", "content": "first"},
  {"tool": "write", "status": "success", "content": "second"},
  {"tool": "read", "status": "success", "content": "third"}
]
</results>"""
    events = []
    async for event in parse_tokens(xml):
        events.append(event)

    results = json.loads(events[0]["content"])
    assert results[0]["content"] == "first"
    assert results[1]["content"] == "second"
    assert results[2]["content"] == "third"


@pytest.mark.asyncio
async def test_no_token_loss_complex_streaming():
    """Complex streaming scenario loses no tokens."""
    tokens = [
        "<th",
        "ink>rea",
        "soning</th",
        "ink><exec",
        'ute>[{"name": "read", "args": {"file',
        '": "test.tx',
        't"}}]</execut',
        "e>",
    ]
    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    types = [e["type"] for e in events]
    assert "think" in types
    assert "call" in types
    assert "execute" in types


@pytest.mark.asyncio
async def test_protocol_example_single_iteration():
    """Parse single iteration — think + execute, then parser stops.

    Complete protocol spans multiple iterations. Each parse pass handles
    one LLM output up to execute. Results are system-injected between iterations.
    """
    xml = """<think>read config, update endpoint, verify</think>

<execute>
[
  {"name": "read", "args": {"file": "config.json"}}
]
</execute>"""
    events = []
    async for event in parse_tokens(xml):
        events.append(event)

    types = [e["type"] for e in events]
    assert types == ["think", "call", "execute"]


@pytest.mark.asyncio
async def test_malformed_json_in_execute():
    """Malformed JSON in execute block produces error event."""
    xml = """<execute>
[{"name": "read", "args": {"file": "test.txt"}}
</execute>"""
    events = []
    async for event in parse_tokens(xml):
        events.append(event)

    has_error = any(e["type"] == "respond" and "Error" in e.get("content", "") for e in events)
    assert has_error


@pytest.mark.asyncio
async def test_execute_missing_name_field():
    """Execute with missing 'name' field produces error."""
    xml = """<execute>
[{"args": {"file": "test.txt"}}]
</execute>"""
    events = []
    async for event in parse_tokens(xml):
        events.append(event)

    has_error = any(e["type"] == "respond" and "Error" in e.get("content", "") for e in events)
    assert has_error


@pytest.mark.asyncio
async def test_execute_missing_args_field():
    """Execute with missing 'args' field produces error."""
    xml = """<execute>
[{"name": "read"}]
</execute>"""
    events = []
    async for event in parse_tokens(xml):
        events.append(event)

    has_error = any(e["type"] == "respond" and "Error" in e.get("content", "") for e in events)
    assert has_error


@pytest.mark.asyncio
async def test_execute_not_json_array():
    """Execute with non-array JSON produces error."""
    xml = """<execute>
{"name": "read", "args": {}}
</execute>"""
    events = []
    async for event in parse_tokens(xml):
        events.append(event)

    has_error = any(e["type"] == "respond" and "Error" in e.get("content", "") for e in events)
    assert has_error


@pytest.mark.asyncio
async def test_execute_array_with_non_object():
    """Execute array with non-object element produces error."""
    xml = """<execute>
[
  {"name": "read", "args": {}},
  "not an object"
]
</execute>"""
    events = []
    async for event in parse_tokens(xml):
        events.append(event)

    has_error = any(e["type"] == "respond" and "Error" in e.get("content", "") for e in events)
    assert has_error


@pytest.mark.asyncio
async def test_empty_execute_array():
    """Empty execute array is valid, produces no calls."""
    xml = """<execute>
[]
</execute>"""
    events = []
    async for event in parse_tokens(xml):
        events.append(event)

    calls = [e for e in events if e["type"] == "call"]
    assert len(calls) == 0
    assert any(e["type"] == "execute" for e in events)


@pytest.mark.asyncio
async def test_whitespace_only_content():
    """Whitespace-only think/results content yields no event."""
    xml = """<think>   </think><results>

</results>"""
    events = []
    async for event in parse_tokens(xml):
        events.append(event)

    assert len(events) == 0


@pytest.mark.asyncio
async def test_parser_terminates_after_execute():
    """Parser MUST stop after <execute> — model cannot bypass tool results.

    This is a critical invariant. Some models (e.g., gpt-5.1) emit their response
    and <end> in the same HTTP call as <execute>, before seeing tool results.
    The parser must terminate after execute to force a new iteration where the
    model sees <results> in context.
    """
    malformed_stream = (
        '<execute>[{"name": "read", "args": {"file": "x"}}]</execute>I already know the answer<end>'
    )

    events = [e async for e in parse_tokens(malformed_stream)]
    event_types = [e["type"] for e in events]

    assert event_types == ["call", "execute"]
    assert "respond" not in event_types
    assert "end" not in event_types
