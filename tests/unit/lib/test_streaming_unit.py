"""Unit tests for XML boundary streaming - Reliability validation."""

from cogency.lib.parsing import parse_xml_sections
from cogency.lib.streaming import validate_streaming


def test_complete_sections():
    """Test parsing of complete XML sections."""
    xml_input = """
        <thinking>
        I need to write a file and then read it back to verify the operation.
        </thinking>

        <tools>
        [{"name": "file_write", "args": {"filename": "test.txt", "content": "42"}},
         {"name": "file_read", "args": {"filename": "test.txt"}}]
        </tools>

        <response>
        I'll execute these file operations now.
        </response>
        """

    result = parse_xml_sections(xml_input)
    assert result.success

    sections = result.unwrap()
    assert "I need to write a file" in sections["thinking"]
    assert "file_write" in sections["tools"]
    assert "execute these file operations" in sections["response"]


def test_missing_sections():
    """Test handling of missing sections."""
    xml_input = """
        <thinking>
        Just thinking, no tools needed.
        </thinking>

        <response>
        Here's my final answer.
        </response>
        """

    result = parse_xml_sections(xml_input)
    assert result.success

    sections = result.unwrap()
    assert sections["thinking"] is not None
    assert sections["tools"] is None
    assert sections["response"] is not None


def test_malformed_xml():
    """Test resilience to malformed XML."""
    test_cases = [
        # Missing closing tag
        "<thinking>Some thought<tools>[]</tools>",
        # Nested tags
        "<thinking>I think <thinking>nested</thinking> thoughts</thinking>",
        # Empty sections
        "<thinking></thinking><tools></tools>",
        # Case variations
        "<THINKING>Upper case</THINKING><tools>[]</tools>",
    ]

    for xml_input in test_cases:
        result = parse_xml_sections(xml_input)
        # Should handle gracefully - either succeed or fail cleanly
        assert result.success or isinstance(result.error, str)


def test_json_in_tools_section():
    """Test JSON parsing within tools section."""
    xml_input = """
        <thinking>Need to use multiple tools</thinking>
        <tools>
        [
            {"name": "file_write", "args": {"filename": "data.json", "content": "{}"}},
            {"name": "shell", "args": {"command": "ls -la"}}
        ]
        </tools>
        <response>Tools executed</response>
        """

    result = parse_xml_sections(xml_input)
    assert result.success

    sections = result.unwrap()
    tools_json = sections["tools"]

    # Should be valid JSON
    import json

    tools = json.loads(tools_json)
    assert len(tools) == 2
    assert tools[0]["name"] == "file_write"
    assert tools[1]["name"] == "shell"


def test_streaming_buffer_updates():
    """Test buffer accumulation during streaming."""
    # Simulate streaming chunks building complete XML
    chunks = [
        "<thinking>I need to",
        " analyze this step by step",
        "</thinking><tools>[",
        '{"name": "file_write", "args": {}}',
        "]</tools><response>",
        "Task completed successfully",
        "</response>",
    ]

    # Final buffer should parse correctly
    final_buffer = "".join(chunks)
    result = parse_xml_sections(final_buffer)

    assert result.success
    sections = result.unwrap()
    assert "analyze this step by step" in sections["thinking"]
    assert "file_write" in sections["tools"]
    assert "Task completed" in sections["response"]


def test_comprehensive_edge_cases():
    """Test comprehensive edge cases for reliability."""
    test_cases = [
        # Basic complete case
        (
            "<thinking>Think</thinking><tools>[]</tools><response>Done</response>",
            {"thinking": "Think", "tools": "[]", "response": "Done"},
        ),
        # Only thinking
        (
            "<thinking>Just thinking</thinking>",
            {"thinking": "Just thinking", "tools": None, "response": None},
        ),
        # Tools with complex JSON
        (
            '<thinking>Complex</thinking><tools>[{"name":"test","args":{"data":{"nested":true}}}]</tools>',
            {
                "thinking": "Complex",
                "tools": '[{"name":"test","args":{"data":{"nested":true}}}]',
                "response": None,
            },
        ),
        # Whitespace handling
        (
            "  <thinking>  Spaced  </thinking>  <tools>  []  </tools>  ",
            {"thinking": "Spaced", "tools": "[]", "response": None},
        ),
        # Case insensitive
        (
            "<THINKING>Upper</THINKING><tools>[]</tools>",
            {"thinking": "Upper", "tools": "[]", "response": None},
        ),
        # Unicode content
        (
            "<thinking>Unicode: 中文 🎯</thinking><tools>[]</tools>",
            {"thinking": "Unicode: 中文 🎯", "tools": "[]", "response": None},
        ),
        # Malformed JSON in tools (should handle gracefully)
        (
            '<thinking>Bad JSON</thinking><tools>[{"name":"tool", "broken": }</tools>',
            {"thinking": "Bad JSON", "tools": '[{"name":"tool", "broken": }', "response": None},
        ),
    ]

    assert validate_streaming(test_cases)


def test_streaming_thinking_extraction():
    """Test extraction of thinking content during streaming."""
    # This would test the real-time thinking extraction
    # Implementation depends on actual streaming mock
    pass


def test_llm_streaming_fallback():
    """Test fallback when LLM doesn't support streaming."""

    # Mock LLM without streaming support
    class MockLLM:
        async def generate(self, messages):
            from cogency.lib.result import Ok

            return Ok("<thinking>Mock thought</thinking><response>Mock response</response>")

    # Test would verify fallback behavior
    # Implementation needs async test setup
    pass


def test_streaming_error_handling():
    """Test error handling during streaming."""

    # Mock LLM that fails during streaming
    class MockFailingLLM:
        async def generate_stream(self, messages):
            from cogency.lib.result import Err

            yield Err("Stream connection lost")

    # Test would verify graceful error handling
    pass


def test_large_thinking_sections():
    """Test handling of very large thinking sections."""
    # Generate large thinking content
    large_thinking = "A" * 10000  # 10KB thinking section
    xml_input = f"<thinking>{large_thinking}</thinking><response>Done</response>"

    result = parse_xml_sections(xml_input)
    assert result.success

    sections = result.unwrap()
    assert len(sections["thinking"]) == 10000


def test_many_tools_section():
    """Test handling of large tools arrays."""
    # Generate large tools array
    tools_array = [{"name": f"tool_{i}", "args": {}} for i in range(100)]
    import json

    tools_json = json.dumps(tools_array)

    xml_input = f"<thinking>Many tools</thinking><tools>{tools_json}</tools>"

    result = parse_xml_sections(xml_input)
    assert result.success

    sections = result.unwrap()
    parsed_tools = json.loads(sections["tools"])
    assert len(parsed_tools) == 100


if __name__ == "__main__":
    # Quick validation run
    test_cases = [
        (
            "<thinking>Test</thinking><tools>[]</tools><response>Done</response>",
            {"thinking": "Test", "tools": "[]", "response": "Done"},
        ),
        (
            "<thinking>Only thinking</thinking>",
            {"thinking": "Only thinking", "tools": None, "response": None},
        ),
    ]

    if validate_streaming(test_cases):
        print("✅ Canonical streaming validation PASSED")
    else:
        print("❌ Canonical streaming validation FAILED")
