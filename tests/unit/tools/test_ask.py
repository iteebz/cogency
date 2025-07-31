import asyncio
from unittest.mock import patch

import pytest

from cogency.tools.ask import Ask


@pytest.fixture
def ask_tool():
    return Ask()


@pytest.mark.asyncio
async def test_ask_tool_approved(ask_tool):
    with patch("builtins.input", return_value="yes"):
        result = await ask_tool.run(prompt="Do you approve?")
        assert result.success is True
        assert result.data["approved"] is True
        assert result.data["response"] == "User approved."


@pytest.mark.asyncio
async def test_ask_tool_denied(ask_tool):
    with patch("builtins.input", return_value="no"):
        result = await ask_tool.run(prompt="Do you approve?")
        assert result.success is False
        assert result.error == "User denied the action."


@pytest.mark.asyncio
async def test_ask_tool_invalid_input(ask_tool):
    with patch("builtins.input", return_value="maybe"):
        result = await ask_tool.run(prompt="Do you approve?")
        assert result.success is False
        assert result.error == "User denied the action."
