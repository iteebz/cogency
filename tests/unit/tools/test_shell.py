"""Shell tool tests."""

import tempfile

import pytest

from cogency.tools.shell import Shell


@pytest.mark.asyncio
async def test_basic():
    tool = Shell()

    result = await tool.run(command="echo hello")
    assert result.success
    assert result.data["exit_code"] == 0
    assert "hello" in result.data["stdout"]
    assert result.data["stderr"] == ""


@pytest.mark.asyncio
async def test_failure():
    tool = Shell()

    result = await tool.run(command="exit 1")
    assert result.success  # Command executed successfully
    assert result.data["exit_code"] == 1
    assert not result.data["success"]


@pytest.mark.asyncio
async def test_timeout():
    import asyncio
    from unittest.mock import AsyncMock, Mock, patch

    tool = Shell()

    # Mock subprocess that never completes
    mock_process = Mock()
    mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
    mock_process.kill = Mock()  # Synchronous kill
    mock_process.wait = AsyncMock(return_value=None)

    with patch("asyncio.create_subprocess_shell", return_value=mock_process):
        result = await tool.run(command="sleep 10", timeout=0.1)

    assert not result.success
    assert "timed out" in result.error


@pytest.mark.asyncio
async def test_working_dir():
    with tempfile.TemporaryDirectory() as temp_dir:
        tool = Shell()

        result = await tool.run(command="pwd", working_dir=temp_dir)
        assert result.success
        assert temp_dir in result.data["stdout"]


@pytest.mark.asyncio
async def test_env():
    tool = Shell()

    result = await tool.run(command="echo $TEST_VAR", env={"TEST_VAR": "hello"})
    assert result.success
    assert "hello" in result.data["stdout"]


@pytest.mark.asyncio
async def test_errors():
    tool = Shell()

    # Invalid working directory
    result = await tool.run(command="echo test", working_dir="/nonexistent")
    assert not result.success

    # System directory blocked - /etc should pass as it's readable, try /bin instead
    result = await tool.run(command="echo test", working_dir="/bin")
    assert not result.success
    assert "forbidden" in result.error
