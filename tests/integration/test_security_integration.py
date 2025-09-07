"""Security integration tests - test interaction between security layers."""

import pytest


class TestShellToolSecurityIntegration:
    """Test shell tool security layer interactions."""

    @pytest.fixture
    def shell_tool(self):
        from cogency.tools.system.shell import SystemShell

        return SystemShell()

    @pytest.mark.asyncio
    async def test_dangerous_system_paths_blocked(self, shell_tool):
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
            assert result.failure, f"Command should be blocked: {cmd}"
            assert "system paths or dangerous operations" in result.error

    @pytest.mark.asyncio
    async def test_legitimate_commands_pass(self, shell_tool):
        """Legitimate commands must pass validation."""
        legitimate_commands = [
            "ls -la",
            "pwd",
            "echo 'hello world'",
            "find . -name '*.py'",
        ]

        for cmd in legitimate_commands:
            result = await shell_tool.execute(cmd, sandbox=True)
            # Should pass validation (may fail execution due to missing files, but not security)
            if result.failure:
                assert "system paths or dangerous operations" not in result.error
                assert "not allowed" not in result.error

    @pytest.mark.asyncio
    async def test_layered_security_integration(self, shell_tool):
        """Test that all security layers work together."""
        # Command injection - blocked by shell sanitizer
        result1 = await shell_tool.execute("ls; rm -rf /", sandbox=True)
        assert result1.failure
        assert "Invalid shell command syntax" in result1.error

        # Unknown command - blocked by whitelist
        result2 = await shell_tool.execute("malicious_binary", sandbox=True)
        assert result2.failure
        assert "not allowed" in result2.error

        # System path in allowed command - blocked by argument validation
        result3 = await shell_tool.execute("cat /etc/passwd", sandbox=True)
        assert result3.failure
        assert "system paths or dangerous operations" in result3.error

    @pytest.mark.asyncio
    async def test_sandbox_vs_non_sandbox_behavior(self, shell_tool):
        """Argument validation should work in both sandbox and non-sandbox mode."""
        dangerous_cmd = "cat /etc/passwd"

        # Should be blocked in sandbox mode
        result1 = await shell_tool.execute(dangerous_cmd, sandbox=True)
        assert result1.failure

        # Should also be blocked in non-sandbox mode
        result2 = await shell_tool.execute(dangerous_cmd, sandbox=False)
        assert result2.failure
