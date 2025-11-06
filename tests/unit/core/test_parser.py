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
async def test_execute_single_tool():
    """Parse execute block with single tool."""
    xml = """<execute>
        <read><file>test.txt</file></read>
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
async def test_execute_multiple_tools():
    """Parse execute block with multiple tools - order preserved."""
    xml = """<execute>
        <read><file>a.txt</file></read>
        <write><file>b.txt</file><content>x</content></write>
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


@pytest.mark.asyncio
async def test_results_block():
    """Parse results block."""
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
async def test_full_sequence_think_execute_results():
    """Parse full protocol sequence."""
    xml = """<think>reading config and updating endpoint</think>
<execute>
  <read><file>config.json</file></read>
</execute>
<results>
[{"tool": "read", "status": "success", "content": {"api": "old.com"}}]
</results>"""
    events = []
    async for event in parse_tokens(xml):
        events.append(event)

    types = [e["type"] for e in events]
    assert types == ["think", "call", "execute", "result"]


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
    """Mixed tags across streaming tokens preserve order."""
    tokens = [
        "<think>reasoning</think>",
        "<execute><read><file>test.txt</file></read></execute>",
        '<results>[{"tool": "read", "status": "success"}]</results>',
    ]
    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    types = [e["type"] for e in events]
    assert types.index("think") < types.index("call")
    assert types.index("call") < types.index("execute")
    assert types.index("execute") < types.index("result")


@pytest.mark.asyncio
async def test_execute_order_preserved_multiple_tools():
    """Multiple tools in execute block produce calls in order."""
    xml = """<execute>
        <read><file>1.txt</file></read>
        <write><file>2.txt</file><content>x</content></write>
        <read><file>3.txt</file></read>
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
        "ute><read><file",
        ">test.tx",
        "t</file></read></execut",
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
async def test_protocol_example_complete_sequence():
    """Parse complete protocol example from spec."""
    xml = """<think>read config, update endpoint, verify</think>

<execute>
  <read><file>config.json</file></read>
</execute>

<results>
[{"tool": "read", "status": "success", "content": {"api": "old.com"}}]
</results>

<think>writing updated config and verifying in one batch</think>

<execute>
  <write><file>config.json</file><content>{"api": "new.com"}</content></write>
  <read><file>config.json</file></read>
</execute>

<results>
[
  {"tool": "write", "status": "success", "content": {"bytes": 22}},
  {"tool": "read", "status": "success", "content": {"api": "new.com"}}
]
</results>"""
    events = []
    async for event in parse_tokens(xml):
        events.append(event)

    types = [e["type"] for e in events]
    think_count = types.count("think")
    call_count = types.count("call")
    execute_count = types.count("execute")
    result_count = types.count("result")

    assert think_count == 2
    assert call_count == 3
    assert execute_count == 2
    assert result_count == 2
