"""Executor tests - reference-grade tool execution validation."""

from unittest.mock import MagicMock

import pytest

from cogency.core.config import Config
from cogency.core.executor import execute, execute_calls
from cogency.core.protocols import Tool, ToolResult
from cogency.core.result import Err, Ok


class MockTool(Tool):
    """Test tool for executor validation."""

    @property
    def name(self) -> str:
        return "mock"

    @property
    def description(self) -> str:
        return "Test tool"

    @property
    def schema(self) -> dict:
        return {"arg": {}}

    async def execute(self, arg: str = "default", **kwargs):
        if arg == "fail":
            return Err("Tool failed")
        if arg == "crash":
            raise RuntimeError("Tool crashed")
        return Ok(ToolResult(outcome=f"executed with {arg}", content=f"details: {arg}"))


@pytest.fixture
def config():
    """Config with mock tool."""
    from cogency.core.protocols import LLM, Storage

    class MockLLM(LLM):
        async def generate(self, messages):
            from cogency.core.result import Ok

            return Ok("Generated response")

        async def connect(self, messages):
            from cogency.core.result import Ok

            return Ok("connection")

        async def stream(self, connection):
            yield "token"

        async def send(self, session, content):
            return True

        async def receive(self, session):
            yield "received"

        async def close(self, session):
            return True

    class MockStorage(Storage):
        async def save_message(self, conversation_id, user_id, type, content, timestamp=None):
            return True

        async def load_messages(self, conversation_id, include=None, exclude=None):
            return []

        async def save_profile(self, user_id, profile):
            return True

        async def load_profile(self, user_id):
            return {}

    return Config(llm=MockLLM(), storage=MockStorage(), tools=[MockTool()], sandbox=True)


@pytest.mark.asyncio
async def test_successful_execution(config):
    """Tool executes successfully with proper result structure."""
    call = {"name": "mock", "args": {"arg": "test_value"}}

    result = await execute(call, config, "user1", "conv1")

    assert isinstance(result, ToolResult)
    assert result.outcome == "executed with test_value"
    assert result.content == "details: test_value"


@pytest.mark.asyncio
async def test_tool_not_found(config):
    """Missing tool returns proper error."""
    call = {"name": "nonexistent", "args": {}}

    result = await execute(call, config, "user1", "conv1")

    assert result.outcome == "nonexistent not found: Tool 'nonexistent' not registered"


@pytest.mark.asyncio
async def test_missing_tool_name(config):
    """Call without tool name returns validation error."""
    call = {"args": {"arg": "test"}}

    result = await execute(call, config, "user1", "conv1")

    assert result.outcome == "missing tool name"


@pytest.mark.asyncio
async def test_invalid_call_format(config):
    """Non-dict call returns format error."""
    result = await execute("invalid", config, "user1", "conv1")

    assert result.outcome == "invalid call format"


@pytest.mark.asyncio
async def test_invalid_args_format(config):
    """Non-dict args return validation error."""
    call = {"name": "mock", "args": "invalid"}

    result = await execute(call, config, "user1", "conv1")

    assert result.outcome == "mock invalid args"


@pytest.mark.asyncio
async def test_tool_execution_failure(config):
    """Tool returning Err() handled properly."""
    call = {"name": "mock", "args": {"arg": "fail"}}

    result = await execute(call, config, "user1", "conv1")

    assert result.outcome == "mock failed: Tool failed"


@pytest.mark.asyncio
async def test_tool_crash(config):
    """Exception during execution handled gracefully."""
    call = {"name": "mock", "args": {"arg": "crash"}}

    result = await execute(call, config, "user1", "conv1")

    assert result.outcome == "mock crashed: Tool crashed"


@pytest.mark.asyncio
async def test_context_injection():
    """Global context (sandbox, user_id) injected into tool args."""
    from cogency.core.protocols import LLM, Storage

    mock_tool = MagicMock()
    mock_tool.name = "context_tool"
    mock_tool.execute = MagicMock(return_value=Ok(ToolResult(outcome="success")))

    class MockLLM(LLM):
        async def generate(self, messages):
            from cogency.core.result import Ok

            return Ok("Generated")

        async def connect(self, messages):
            from cogency.core.result import Ok

            return Ok("connection")

        async def stream(self, connection):
            yield "token"

        async def send(self, session, content):
            return True

        async def receive(self, session):
            yield "received"

        async def close(self, session):
            return True

    class MockStorage(Storage):
        async def save_message(self, *args, **kwargs):
            return True

        async def load_messages(self, *args, **kwargs):
            return []

        async def save_profile(self, *args, **kwargs):
            return True

        async def load_profile(self, *args, **kwargs):
            return {}

    config = Config(llm=MockLLM(), storage=MockStorage(), tools=[mock_tool], sandbox=True)

    call = {"name": "context_tool", "args": {"explicit_arg": "value"}}

    await execute(call, config, "test_user", "test_conv")

    mock_tool.execute.assert_called_once_with(
        explicit_arg="value", sandbox=True, user_id="test_user"
    )


@pytest.mark.asyncio
async def test_execute_calls_multiple():
    """execute_calls processes list of calls sequentially."""
    from cogency.core.protocols import LLM, Storage

    class MockLLM(LLM):
        async def generate(self, messages):
            from cogency.core.result import Ok

            return Ok("Generated")

        async def connect(self, messages):
            from cogency.core.result import Ok

            return Ok("connection")

        async def stream(self, connection):
            yield "token"

        async def send(self, session, content):
            return True

        async def receive(self, session):
            yield "received"

        async def close(self, session):
            return True

    class MockStorage(Storage):
        async def save_message(self, *args, **kwargs):
            return True

        async def load_messages(self, *args, **kwargs):
            return []

        async def save_profile(self, *args, **kwargs):
            return True

        async def load_profile(self, *args, **kwargs):
            return {}

    config = Config(llm=MockLLM(), storage=MockStorage(), tools=[MockTool()])

    calls = [
        {"name": "mock", "args": {"arg": "first"}},
        {"name": "mock", "args": {"arg": "second"}},
    ]

    results = await execute_calls(calls, config, "user1", "conv1")

    assert len(results) == 2
    assert results[0].outcome == "executed with first"
    assert results[1].outcome == "executed with second"


@pytest.mark.asyncio
async def test_execute_calls_handles_failures():
    """execute_calls continues on individual failures."""
    from cogency.core.protocols import LLM, Storage

    class MockLLM(LLM):
        async def generate(self, messages):
            from cogency.core.result import Ok

            return Ok("Generated")

        async def connect(self, messages):
            from cogency.core.result import Ok

            return Ok("connection")

        async def stream(self, connection):
            yield "token"

        async def send(self, session, content):
            return True

        async def receive(self, session):
            yield "received"

        async def close(self, session):
            return True

    class MockStorage(Storage):
        async def save_message(self, *args, **kwargs):
            return True

        async def load_messages(self, *args, **kwargs):
            return []

        async def save_profile(self, *args, **kwargs):
            return True

        async def load_profile(self, *args, **kwargs):
            return {}

    config = Config(llm=MockLLM(), storage=MockStorage(), tools=[MockTool()])

    calls = [
        {"name": "mock", "args": {"arg": "success"}},
        {"name": "mock", "args": {"arg": "fail"}},
        {"name": "mock", "args": {"arg": "another_success"}},
    ]

    results = await execute_calls(calls, config, "user1", "conv1")

    assert len(results) == 3
    assert results[0].outcome == "executed with success"
    assert results[1].outcome == "mock failed: Tool failed"
    assert results[2].outcome == "executed with another_success"
