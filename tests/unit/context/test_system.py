from cogency.context.system import prompt
from cogency.tools import Write


def test_default_identity():
    result = prompt()

    assert "IDENTITY" in result
    assert "Cogency: autonomous reasoning agent" in result
    assert "autonomous reasoning agent" in result


def test_identity_override():
    custom_identity = "You are a Zealot. Skeptical cothinking partner."
    result = prompt(identity=custom_identity)

    # Custom identity should be present
    assert "You are a Zealot" in result
    assert "Skeptical cothinking partner" in result

    # Default identity should not be present
    assert "You are Cogency" not in result
    assert "autonomous reasoning agent" not in result


def test_prompt_section_order():
    custom_identity = "CUSTOM IDENTITY SECTION"
    custom_instructions = "CUSTOM INSTRUCTIONS SECTION"
    tools = [Write]

    result = prompt(
        identity=custom_identity,
        instructions=custom_instructions,
        tools=tools,
    )

    # Find positions of each section
    identity_pos = result.find("CUSTOM IDENTITY SECTION")
    protocol_pos = result.find("PROTOCOL")
    examples_pos = result.find("EXAMPLES")
    security_pos = result.find("SECURITY")
    instructions_pos = result.find("CUSTOM INSTRUCTIONS SECTION")
    tools_pos = result.find("TOOLS:")  # Look for the actual tools section

    # Verify order: identity < protocol < examples < security < instructions < tools
    assert protocol_pos < identity_pos
    assert protocol_pos < examples_pos
    assert examples_pos < security_pos
    assert security_pos < instructions_pos
    assert instructions_pos < tools_pos


def test_instructions_optional():
    # Without instructions
    result_without = prompt(identity="Custom identity")
    assert "INSTRUCTIONS:" not in result_without

    # With instructions
    result_with = prompt(identity="Custom identity", instructions="Custom instructions")
    assert "INSTRUCTIONS: Custom instructions" in result_with


def test_security_always_present():
    # Security is always included
    result = prompt()
    assert "SECURITY" in result

    # Security present with custom options
    result_custom = prompt(identity="Custom", instructions="Instructions")
    assert "SECURITY" in result_custom


def test_protocol_always_present():
    # Various combinations should all include protocol with JSON array format
    test_cases = [
        prompt(),
        prompt(identity="Custom"),
        prompt(instructions="Custom"),
        prompt(identity="Custom", instructions="Custom"),
    ]

    for result in test_cases:
        assert "PROTOCOL" in result
        assert "<execute>" in result
        assert "</execute>" in result
        assert '{"name":' in result
        assert '"args":' in result


def test_tools_section():
    tools = [Write]

    # With tools
    result_with_tools = prompt(tools=tools)
    assert "write" in result_with_tools
    assert "Write file." in result_with_tools

    # Without tools
    result_without_tools = prompt(tools=None)
    assert "No tools available" in result_without_tools
