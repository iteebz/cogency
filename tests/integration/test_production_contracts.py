"""Production-grade contracts: Verify system behavior under failure conditions.

These tests ensure Cogency behaves correctly in scenarios that would cause
production failures:
- Observability failures don't crash execution
- Storage corruption is properly reported
- Tool failures trigger circuit breaker
- Context memory is bounded
- WebSocket failures fallback to HTTP
"""

import json
from typing import TYPE_CHECKING, cast

import pytest

from cogency import Agent

if TYPE_CHECKING:
    from cogency.core.protocols import ResultEvent


@pytest.mark.asyncio
async def test_telemetry_failure_doesnt_crash_agent(mock_config, mock_llm, mock_tool):
    """Agent continues even if telemetry persistence fails.

    Contract: Non-critical observability failures must not crash execution.
    """
    mock_tool_instance = mock_tool()
    protocol_tokens = [
        f'<execute>[{{"name": "{mock_tool_instance.name}", "args": {{"message": "test"}}}}]</execute>',
        "Done",
    ]

    class FailingTelemetryStorage:
        """Storage that fails on save_event (telemetry)."""

        def __init__(self, base_storage):
            self.base = base_storage

        async def save_message(self, *args, **kwargs):
            return await self.base.save_message(*args, **kwargs)

        async def save_event(self, *args, **kwargs):
            raise RuntimeError("Telemetry database unavailable")

        async def load_messages(self, *args, **kwargs):
            return await self.base.load_messages(*args, **kwargs)

        async def save_profile(self, *args, **kwargs):
            return await self.base.save_profile(*args, **kwargs)

        async def load_profile(self, *args, **kwargs):
            return await self.base.load_profile(*args, **kwargs)

        async def count_user_messages(self, *args, **kwargs):
            return await self.base.count_user_messages(*args, **kwargs)

        async def load_user_messages(self, *args, **kwargs):
            return await self.base.load_user_messages(*args, **kwargs)

        async def save_request(self, *args, **kwargs):
            return await self.base.save_request(*args, **kwargs)

    llm = mock_llm.set_response_tokens(protocol_tokens)
    storage = FailingTelemetryStorage(mock_config.storage)

    agent = Agent(
        llm=llm,
        tools=[mock_tool_instance],
        storage=storage,  # type: ignore[arg-type]
        mode="replay",
        max_iterations=1,
    )

    # Should NOT raise - telemetry failure is non-critical
    events = [event async for event in agent("Test query")]

    # Verify execution succeeded despite telemetry failure
    result_events = [e for e in events if e["type"] == "result"]
    assert len(result_events) > 0
    result_event = cast("ResultEvent", result_events[0])
    assert result_event["type"] == "result"
    payload = result_event["payload"]
    assert payload is not None
    assert payload["success_count"] == 1


@pytest.mark.asyncio
async def test_circuit_breaker_stops_runaway_agent(mock_llm, mock_tool):
    """After 3 consecutive tool failures, agent terminates with 'end' event.

    Contract: Circuit breaker prevents runaway agents from infinite loop of
    tool failures.
    """
    failing_tool = mock_tool().configure(
        name="failing_tool", description="Always fails", should_fail=True
    )

    batched_execute = (
        f"<execute>["
        f'{{"name": "{failing_tool.name}", "args": {{}}}},'
        f'{{"name": "{failing_tool.name}", "args": {{}}}},'
        f'{{"name": "{failing_tool.name}", "args": {{}}}}'
        f"]</execute>"
    )

    llm = mock_llm.set_response_tokens([batched_execute])
    agent = Agent(llm=llm, tools=[failing_tool], mode="replay", max_iterations=10)

    events = [event async for event in agent("Test query")]

    event_types = [e["type"] for e in events]
    assert "end" in event_types

    call_count = event_types.count("call")
    assert call_count == 3


@pytest.mark.asyncio
async def test_resume_fallback_to_replay_on_missing_provider(mock_tool):
    """Auto mode falls back from resume to replay when LLM lacks WebSocket.

    Contract: Auto mode gracefully degrades to replay when WebSocket unavailable.
    """
    mock_tool_instance = mock_tool()

    class NoWebSocketLLM:
        """LLM without WebSocket capability."""

        http_model = "mock"

        async def stream(self, messages):
            yield f'<execute>[{{"name": "{mock_tool_instance.name}", "args": {{"message": "test"}}}}]</execute>'
            yield "Done"

        async def generate(self, messages):
            return f'<execute>[{{"name": "{mock_tool_instance.name}", "args": {{"message": "test"}}}}]</execute>Done'

        async def close(self):
            pass

    llm = NoWebSocketLLM()
    agent = Agent(llm=llm, tools=[mock_tool_instance], mode="auto", max_iterations=1)  # type: ignore[arg-type]

    # Should NOT raise - should fallback to replay
    events = [event async for event in agent("Test query")]

    # Verify execution succeeded despite no WebSocket
    result_events = [e for e in events if e["type"] == "result"]
    assert len(result_events) > 0


@pytest.mark.asyncio
async def test_storage_load_error_propagates(mock_config):
    """Storage load failure raises exception to agent boundary.

    Contract: Critical path storage errors must bubble up, not be silently
    swallowed.
    """
    from cogency.context.assembly import assemble

    class FailingStorage:
        """Storage that fails on load_messages."""

        async def save_message(self, *args, **kwargs):
            raise NotImplementedError

        async def load_messages(self, *args, **kwargs):
            raise RuntimeError("Database checksum mismatch - data corrupted")

        async def save_event(self, *args, **kwargs):
            raise NotImplementedError

        async def save_request(self, *args, **kwargs):
            raise NotImplementedError

        async def save_profile(self, *args, **kwargs):
            raise NotImplementedError

        async def load_profile(self, *args, **kwargs):
            return {}

        async def count_user_messages(self, *args, **kwargs):
            return 0

        async def load_user_messages(self, *args, **kwargs):
            return []

    with pytest.raises(RuntimeError, match="corrupted"):
        await assemble(
            user_id="test",
            conversation_id="conv",
            tools=[],
            storage=FailingStorage(),  # type: ignore[arg-type]
            history_window=None,
            history_transform=None,
            profile_enabled=False,
        )


@pytest.mark.asyncio
async def test_tool_error_fed_back_to_llm(mock_llm, mock_tool):
    """Tool failure returned as result, not silently ignored.

    Contract: Tool execution errors are visible to agent via result event,
    allowing self-correction.
    """
    failing_tool = mock_tool().configure(name="failing_tool", description="Fails", should_fail=True)

    protocol_tokens = [
        f'<execute>[{{"name": "{failing_tool.name}", "args": {{}}}}]</execute>',
        "Tool failed. Trying alternate approach.",
    ]

    llm = mock_llm.set_response_tokens(protocol_tokens)
    agent = Agent(llm=llm, tools=[failing_tool], mode="replay", max_iterations=1)

    events = [event async for event in agent("Test query")]

    # Verify result event shows failure
    result_events = [e for e in events if e["type"] == "result"]
    assert len(result_events) > 0

    result = result_events[0]
    result_typed = cast("ResultEvent", result)
    assert result_typed["type"] == "result"
    content = result_typed.get("content", "")
    results_json = json.loads(content)
    assert results_json[0]["status"] == "failure"
    payload = result_typed["payload"]
    assert payload is not None
    assert payload["failure_count"] == 1


@pytest.mark.asyncio
async def test_semantic_security_in_system_prompt(mock_config):
    """System prompt includes semantic security constraints for LLM.

    Contract: LLM has explicit security guidance in every execution, not just
    pattern validation at tool boundary.
    """
    from cogency.context.system import prompt

    system_msg = prompt(tools=[], identity=None, instructions=None)

    # Semantic security constraints should be in prompt
    assert "SECURITY" in system_msg
    assert "Project scope only" in system_msg or "system paths" in system_msg.lower()
    assert (
        "/etc" in system_msg or "/root" in system_msg or "system directories" in system_msg.lower()
    )


@pytest.mark.asyncio
async def test_context_assembly_requires_storage(mock_config):
    """Context assembly fails cleanly if storage unavailable.

    Contract: Missing storage dependency fails immediately, not silently.
    """
    from cogency.context.assembly import assemble

    with pytest.raises((RuntimeError, AttributeError, TypeError)):
        await assemble(
            user_id="test",
            conversation_id="conv",
            tools=[],
            storage=None,  # type: ignore[arg-type]  # Missing storage
            history_window=None,
            history_transform=None,
            profile_enabled=False,
        )
