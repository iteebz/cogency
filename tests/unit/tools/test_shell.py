"""Test Shell tool business logic."""

import pytest

from cogency.tools.shell import Shell


@pytest.mark.asyncio
async def test_interface():
    shell = Shell()

    assert shell.name == "shell"
    assert shell.description
    assert hasattr(shell, "run")

    schema = shell.schema
    examples = shell.examples
    assert isinstance(schema, str) and len(schema) > 0
    assert isinstance(examples, list) and len(examples) > 0


@pytest.mark.asyncio
async def test_blocked_command():
    shell = Shell()

    result = await shell.run(command="rm -rf /")
    assert not result.success
    assert "blocked for security" in result.error


@pytest.mark.asyncio
async def test_safe_command():
    shell = Shell()

    result = await shell.run(command="echo hello")
    assert result.success
    assert result.data["exit_code"] == 0
    assert result.data["stdout"]
    assert result.data["stderr"] == ""
