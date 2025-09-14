"""Security integration tests - security layers working together."""

import pytest


@pytest.fixture
def shell_tool():
    from cogency.tools.system.shell import SystemShell

    return SystemShell()


@pytest.mark.asyncio
async def test_dangerous_paths_blocked(shell_tool):
    """Shell tool must block commands with dangerous system paths."""
    dangerous_commands = [
        "cat /etc/passwd",
        "cat /etc/shadow",
        "find / -name '*.key'",
        "ls /bin/bash",
        "cp file.txt ~/.ssh/authorized_keys",
    ]

    for cmd in dangerous_commands:
        result = await shell_tool.execute(cmd, sandbox=True)
        assert "system paths or dangerous operations" in result.outcome, f"Command should be blocked: {cmd}"


@pytest.mark.asyncio
async def test_legitimate_commands_pass(shell_tool):
    """Legitimate commands must pass validation."""
    legitimate_commands = [
        "ls -la",
        "pwd",
        "echo 'hello world'",
        "find . -name '*.py'",
    ]

    for cmd in legitimate_commands:
        result = await shell_tool.execute(cmd, sandbox=True)
        # Should pass security validation (may fail execution, but not security)
        assert "system paths or dangerous operations" not in result.outcome, f"Legitimate command blocked: {cmd}"
        assert "Invalid command syntax" not in result.outcome, f"Legitimate command blocked: {cmd}"


@pytest.mark.asyncio
async def test_layered_security(shell_tool):
    """Test that all security layers work together."""
    # Command injection - blocked by shell sanitizer
    result1 = await shell_tool.execute("ls; rm -rf /", sandbox=True)
    assert "Invalid command syntax" in result1.outcome
    
    # Unknown command - blocked by whitelist
    result2 = await shell_tool.execute("malicious_binary", sandbox=True)
    assert "not allowed" in result2.outcome
    
    # System path in allowed command - blocked by argument validation
    result3 = await shell_tool.execute("cat /etc/passwd", sandbox=True)
    assert "system paths or dangerous operations" in result3.outcome


@pytest.mark.asyncio
async def test_sandbox_modes(shell_tool):
    """Argument validation should work in both sandbox and non-sandbox mode."""
    dangerous_cmd = "cat /etc/passwd"

    # Should be blocked in sandbox mode
    result1 = await shell_tool.execute(dangerous_cmd, sandbox=True)
    assert "system paths or dangerous operations" in result1.outcome

    # Should also be blocked in non-sandbox mode  
    result2 = await shell_tool.execute(dangerous_cmd, sandbox=False)
    assert "system paths or dangerous operations" in result2.outcome
