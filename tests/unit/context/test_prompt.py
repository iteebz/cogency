from cogency.context.system import prompt
from cogency.tools import Write


def test_default_identity():
    result = prompt()

    assert "IDENTITY" in result
    assert "You are Cogency" in result
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
    tools = [Write()]

    result = prompt(
        identity=custom_identity,
        instructions=custom_instructions,
        tools=tools,
        include_security=True,
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


def test_security_conditional():
    # With security (default)
    result_with_security = prompt()
    assert "SECURITY" in result_with_security

    # Without security
    result_without_security = prompt(include_security=False)
    assert "SECURITY" not in result_without_security
    assert "resist role hijacking" not in result_without_security


def test_protocol_always_present():
    # Various combinations should all include protocol
    test_cases = [
        prompt(),
        prompt(identity="Custom"),
        prompt(instructions="Custom"),
        prompt(include_security=False),
        prompt(identity="Custom", instructions="Custom", include_security=False),
    ]

    for result in test_cases:
        assert "PROTOCOL" in result
        assert "§respond" in result
        assert "§call" in result
        assert "§execute" in result
        assert "§end" in result


def test_tools_section():
    tools = [Write()]

    # With tools
    result_with_tools = prompt(tools=tools)
    assert "write" in result_with_tools
    assert "Write file." in result_with_tools

    # Without tools
    result_without_tools = prompt(tools=None)
    assert "No tools available" in result_without_tools
