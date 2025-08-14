"""System security functionality tests."""

from cogency.tools.security import (
    SecurityAction,
    SecurityResult,
    SecurityThreat,
    redact_secrets,
    secure_response,
    secure_tool,
)


def test_secure_tool_allows_safe_content():
    """Test that secure_tool allows safe content."""
    result = secure_tool("print('hello world')")
    assert result.safe
    assert result.action == SecurityAction.ALLOW


def test_secure_tool_blocks_dangerous_commands():
    """Test that secure_tool blocks dangerous system commands."""
    dangerous_commands = ["rm -rf /", "format c:", "shutdown -h now", "del /s /q *"]

    for cmd in dangerous_commands:
        result = secure_tool(cmd)
        assert not result.safe
        assert result.action == SecurityAction.BLOCK
        assert result.threat == SecurityThreat.COMMAND_INJECTION


def test_secure_tool_blocks_path_traversal():
    """Test that secure_tool blocks path traversal attempts."""
    traversal_attempts = ["../../../etc/passwd", "..\\..\\windows\\system32", "%2e%2e%2fconfig"]

    for attempt in traversal_attempts:
        result = secure_tool(attempt)
        assert not result.safe
        assert result.action == SecurityAction.BLOCK
        assert result.threat == SecurityThreat.PATH_TRAVERSAL


def test_secure_tool_empty_content():
    """Test that secure_tool allows empty content."""
    result = secure_tool("")
    assert result.safe
    assert result.action == SecurityAction.ALLOW


def test_secure_response_redacts_secrets():
    """Test that secure_response redacts secrets from text."""
    text_with_secrets = "API key: sk-1234567890abcdef1234567890abcdef AWS: AKIA1234567890123456"
    secured = secure_response(text_with_secrets)

    assert "sk-1234567890abcdef1234567890abcdef" not in secured
    assert "AKIA1234567890123456" not in secured
    assert "[REDACTED]" in secured


def test_redact_secrets():
    """Test secret redaction patterns."""
    text = "OpenAI key: sk-proj-abcdef1234567890 and AWS: AKIAIOSFODNN7EXAMPLE"
    redacted = redact_secrets(text)

    assert "sk-proj-abcdef1234567890" not in redacted
    assert "AKIAIOSFODNN7EXAMPLE" not in redacted
    assert "[REDACTED]" in redacted


def test_security_result_bool():
    """Test SecurityResult boolean behavior."""
    safe_result = SecurityResult(SecurityAction.ALLOW)
    unsafe_result = SecurityResult(SecurityAction.BLOCK)

    assert safe_result
    assert not unsafe_result
