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
async def test_blocked():
    tool = Shell()

    for cmd in ["rm test", "sudo echo", "kill 123", "shutdown now"]:
        result = await tool.run(command=cmd)
        assert not result.success
        assert "blocked for security" in result.error


@pytest.mark.asyncio
async def test_timeout():
    tool = Shell()

    result = await tool.run(command="sleep 10", timeout=1)
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
