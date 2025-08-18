"""Shell tool tests."""

import subprocess
from unittest.mock import Mock, patch

import pytest

from cogency.tools.shell import Shell


def test_init():
    """Shell initialization."""
    tool = Shell()
    assert tool.name == "shell"
    assert "safe commands" in tool.description.lower()
    assert "python" in tool.description  # Should list available commands


@pytest.mark.asyncio
async def test_execute_success():
    """Shell executes allowed commands."""
    tool = Shell()

    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = "Hello world"
    mock_result.stderr = ""

    with patch("cogency.tools.shell.subprocess.run", return_value=mock_result) as mock_run:
        with patch("cogency.tools.shell.time.time", side_effect=[0.0, 0.5]):
            result = await tool.execute("echo Hello world")

            assert result.success
            assert "Hello world" in result.unwrap()
            assert "exit: 0" in result.unwrap()
            assert "time: 0.5s" in result.unwrap()
            mock_run.assert_called_once()


@pytest.mark.asyncio
async def test_execute_empty_command():
    """Shell rejects empty command."""
    tool = Shell()
    result = await tool.execute("")

    assert result.failure
    assert "empty command" in result.error.lower()


@pytest.mark.asyncio
async def test_execute_empty_parts():
    """Shell rejects whitespace-only command."""
    tool = Shell()
    result = await tool.execute("   ")

    assert result.failure
    assert "empty command" in result.error.lower()


@pytest.mark.asyncio
async def test_execute_forbidden_command():
    """Shell blocks dangerous commands."""
    tool = Shell()
    result = await tool.execute("sudo rm -rf /")

    assert result.failure
    assert "not allowed" in result.error.lower()


@pytest.mark.asyncio
async def test_execute_allowed_commands():
    """Shell allows safe commands."""
    tool = Shell()

    # Check some commands from SAFE_COMMANDS
    allowed_commands = ["ls", "pwd", "python", "git", "npm"]

    for cmd in allowed_commands:
        # Mock successful execution
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = ""

        with patch("cogency.tools.shell.subprocess.run", return_value=mock_result):
            with patch("cogency.tools.shell.time.time", side_effect=[0.0, 0.1]):
                result = await tool.execute(cmd)
                assert result.success, f"Command {cmd} should be allowed"


@pytest.mark.asyncio
async def test_execute_with_stderr():
    """Shell includes stderr in success response."""
    tool = Shell()

    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = "output"
    mock_result.stderr = "warning message"

    with patch("cogency.tools.shell.subprocess.run", return_value=mock_result):
        with patch("cogency.tools.shell.time.time", side_effect=[0.0, 0.1]):
            result = await tool.execute("python --version")

            assert result.success
            assert "output" in result.unwrap()
            assert "STDERR:" in result.unwrap()
            assert "warning message" in result.unwrap()


@pytest.mark.asyncio
async def test_execute_command_failure():
    """Shell handles command execution failure."""
    tool = Shell()

    mock_result = Mock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "command failed"

    with patch("cogency.tools.shell.subprocess.run", return_value=mock_result):
        result = await tool.execute("python nonexistent.py")

        assert result.failure
        assert "exit: 1" in result.error
        assert "command failed" in result.error


@pytest.mark.asyncio
async def test_execute_timeout():
    """Shell handles command timeout."""
    tool = Shell()

    with patch(
        "cogency.tools.shell.subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 30)
    ):
        result = await tool.execute("python infinite_loop.py")

        assert result.failure
        assert "timed out" in result.error.lower()
        assert "30s limit" in result.error


@pytest.mark.asyncio
async def test_execute_command_not_found():
    """Shell handles missing command."""
    tool = Shell()

    with patch("cogency.tools.shell.subprocess.run", side_effect=FileNotFoundError):
        result = await tool.execute("nonexistent_command")

        assert result.failure
        assert "not allowed" in result.error.lower()  # Command validation happens before execution


@pytest.mark.asyncio
async def test_execute_creates_sandbox():
    """Shell ensures sandbox directory exists."""
    tool = Shell()

    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = "output"
    mock_result.stderr = ""

    with patch("cogency.tools.shell.subprocess.run", return_value=mock_result):
        with patch("cogency.tools.shell.Path") as mock_path:
            mock_sandbox = Mock()
            mock_path.return_value = mock_sandbox

            with patch("cogency.tools.shell.time.time", side_effect=[0.0, 0.1]):
                result = await tool.execute("ls")

                mock_sandbox.mkdir.assert_called_once_with(exist_ok=True)
                assert result.success
