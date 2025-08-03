"""API contract validation tests - ensure v1.0.0 compliance."""

import asyncio
from typing import Any, Dict
from unittest.mock import AsyncMock

import pytest
from resilient_result import Result

from cogency import Agent
from cogency.providers.llm.base import LLM
from cogency.tools.base import Tool
from tests.fixtures.llm import MockLLM


class ContractValidatingTool(Tool):
    """Tool that validates contract compliance."""

    def __init__(self):
        super().__init__(
            name="contract_tool",
            description="Tool for testing contracts",
            schema="contract_tool(action='test')",
            emoji="📋",
            examples=["contract_tool(action='validate')"],
            rules=["Must return Result objects"],
        )

    async def run(self, **kwargs) -> Result:
        """Contract: All tools must return Result objects."""
        if "action" not in kwargs:
            return Result.fail("Missing required parameter: action")
        return Result.ok(f"Contract validated: {kwargs['action']}")


class ContractValidatingLLM(LLM):
    """LLM that validates response contracts."""

    def __init__(self, response_data: Dict[str, Any] = None):
        self.response_data = response_data or {"content": "Mock response", "tokens": 10}
        super().__init__("mock", api_keys="test", model="test-model")

    @property
    def default_model(self) -> str:
        return "test-model"

    def _get_client(self):
        return self

    async def _run_impl(self, messages, **kwargs) -> str:
        """Contract: Must return string response."""
        if not isinstance(messages, list):
            raise ValueError("Messages must be a list")
        if not messages:
            raise ValueError("Messages cannot be empty")
        return self.response_data["content"]

    async def _stream_impl(self, messages, **kwargs):
        """Contract: Must yield string chunks."""
        content = self.response_data["content"]
        for char in content:
            yield char


@pytest.mark.asyncio
async def test_tool_interface_contract():
    """Verify all tools comply with Result interface."""
    tool = ContractValidatingTool()

    # Valid call
    result = await tool.run(action="test")
    assert isinstance(result, Result)
    assert result.success
    assert "Contract validated: test" in result.data

    # Invalid call
    result = await tool.run()
    assert isinstance(result, Result)
    assert not result.success
    assert "Missing required parameter" in result.error


@pytest.mark.asyncio
async def test_llm_interface_contract():
    """Verify LLM providers comply with response interface."""
    llm = ContractValidatingLLM()

    # Valid message format
    messages = [{"role": "user", "content": "test"}]
    response = await llm.run(messages)
    assert isinstance(response.data, str)
    assert response.success

    # Stream interface
    chunks = []
    async for chunk in llm.stream(messages):
        chunks.append(chunk)
        assert isinstance(chunk, str)
    assert "".join(chunks) == "Mock response"


@pytest.mark.asyncio
async def test_agent_executor_integration():
    """Test real Agent -> AgentExecutor -> execute_agent flow without mocks."""
    # Use minimal agent configuration to avoid complex preparation
    llm = MockLLM(
        '{"direct_response": "I understand your request and will help you test the contract validation.", "memory": {"content": null, "tags": []}, "selected_tools": [], "mode": "fast", "reasoning": "Simple test query"}'
    )

    agent = Agent(
        name="contract_test",
        llm=llm,
        tools=[],  # No tools to avoid complex tool preparation
        memory=False,
        notify=False,  # Silent mode for clean test output
        mode="fast",  # Skip complex preparation steps
    )

    # Test real execution path
    result = await agent.run_async("Simple test query")

    # Verify response structure
    assert isinstance(result, str)
    assert len(result) > 0
    assert result != "No response generated"  # Should have real response


@pytest.mark.asyncio
async def test_memory_contract_compliance():
    """Verify ImpressionSynthesizer follows storage contracts."""
    from cogency.memory import ImpressionSynthesizer
    from tests.fixtures.store import InMemoryStore

    synthesis_llm = MockLLM('{"preferences": {"style": "concise"}}')
    store = InMemoryStore()
    synthesizer = ImpressionSynthesizer(synthesis_llm, store=store)

    # Test profile creation and persistence
    interaction = {
        "query": "I prefer concise responses",
        "response": "I'll be concise",
        "success": True,
    }

    profile = await synthesizer.update_impression("test_user", interaction)
    assert profile.user_id == "test_user"
    assert profile.interaction_count == 1

    # Test profile loading
    loaded_profile = await synthesizer._load_profile("test_user")
    assert loaded_profile.user_id == "test_user"

    # Test profile context generation
    from cogency.memory.compression import compress

    context = compress(loaded_profile)
    assert isinstance(context, str)


@pytest.mark.asyncio
async def test_state_management_contract():
    """Verify state persistence follows contracts."""
    from cogency.persist.utils import _get_state
    from cogency.state import AgentState

    # Test state creation contract
    state = AgentState("test query")
    assert state.execution.query == "test query"
    assert state.execution.iteration == 0
    assert hasattr(state.execution, "messages")
    assert hasattr(state.execution, "pending_calls")

    # Test state persistence contract (no persistence)
    user_states = {}

    state = await _get_state("user1", "query1", 10, user_states, None)
    assert state is not None
    assert state.execution.query == "query1"


@pytest.mark.asyncio
async def test_error_propagation_contract():
    """Verify errors propagate correctly through the stack."""

    class FailingLLM(MockLLM):
        async def _run_impl(self, messages, **kwargs):
            raise Exception("Deliberate LLM failure")

    agent = Agent(name="error_test", llm=FailingLLM(), tools=[], notify=False)

    # Verify exception propagation
    with pytest.raises(Exception) as exc_info:
        await agent.run_async("test error handling")

    assert "Deliberate LLM failure" in str(exc_info.value)


@pytest.mark.asyncio
async def test_concurrent_agent_isolation():
    """Verify concurrent agents don't interfere with each other."""
    llm1 = MockLLM(
        '{"direct_response": "Response from agent 1", "memory": {"content": null, "tags": []}, "selected_tools": [], "mode": "fast", "reasoning": "Simple query"}'
    )
    llm2 = MockLLM(
        '{"direct_response": "Response from agent 2", "memory": {"content": null, "tags": []}, "selected_tools": [], "mode": "fast", "reasoning": "Simple query"}'
    )

    agent1 = Agent("agent1", llm=llm1, tools=[], notify=False, mode="fast")
    agent2 = Agent("agent2", llm=llm2, tools=[], notify=False, mode="fast")

    # Run concurrently with simple queries
    task1 = asyncio.create_task(agent1.run_async("Simple query 1"))
    task2 = asyncio.create_task(agent2.run_async("Simple query 2"))

    result1, result2 = await asyncio.gather(task1, task2)

    # Verify isolation - each agent gets its own response
    assert result1 == "Response from agent 1"
    assert result2 == "Response from agent 2"
    assert result1 != result2
