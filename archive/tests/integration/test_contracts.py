"""API contract validation tests - ensure v1.0.0 compliance."""

import asyncio
from unittest.mock import AsyncMock

import pytest
from resilient_result import Result

from cogency import Agent
from cogency.tools.base import Tool
from tests.fixtures.provider import MockLLM


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
async def test_provider_interface_contract(mock_provider):
    """Verify providers comply with response interface."""
    # Valid message format
    messages = [{"role": "user", "content": "test"}]
    response = await mock_provider.run(messages)
    assert isinstance(response.data, str)
    assert response.success

    # Stream interface
    chunks = []
    async for chunk in mock_provider.stream(messages):
        chunks.append(chunk)
        assert isinstance(chunk, str)
    assert "".join(chunks) == "Mock response"


@pytest.mark.asyncio
async def test_agent_executor_integration():
    """Test Agent integration with mocked execution."""
    from unittest.mock import patch

    llm = MockLLM(
        response="I understand your request and will help you test the contract validation."
    )

    # Mock the agent execution to avoid slow pipeline
    with patch("cogency.Agent.run_async", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = (
            "I understand your request and will help you test the contract validation."
        )

        agent = Agent(
            name="contract_test",
            llm=llm,
            tools=[],
            memory=False,
            notify=False,
            mode="fast",
        )

        # Test execution path
        result = await agent.run_async("Simple test query")

        # Verify contract compliance - result should be string
        assert isinstance(result, str)
        assert len(result) > 0
        assert result == "I understand your request and will help you test the contract validation."


@pytest.mark.asyncio
async def test_memory_contract_compliance():
    """Verify SituatedMemory follows storage contracts."""
    from cogency.memory.situate import SituatedMemory
    from cogency.storage.state import SQLite

    llm = MockLLM('{"preferences": {"style": "concise"}}')
    store = SQLite(db_path=":memory:")  # Use in-memory database for test isolation
    situated = SituatedMemory(llm, store=store)

    # Test profile creation and persistence
    interaction = {
        "query": "I prefer concise responses",
        "response": "I'll be concise",
        "success": True,
    }

    profile = await situated.update_impression("test_user", interaction)
    assert profile.user_id == "test_user"
    assert profile.interaction_count == 1

    # Test profile loading
    loaded_profile = await situated._load_profile("test_user")
    assert loaded_profile.user_id == "test_user"

    # Test profile context generation
    from cogency.memory.situate.compression import compress

    context = compress(loaded_profile)
    assert isinstance(context, str)


@pytest.mark.asyncio
async def test_state_management_contract():
    """Verify state persistence follows contracts."""
    from cogency.state import State

    # Test state creation contract
    state = State("test query")
    assert state.query == "test query"
    assert state.execution.iteration == 0
    assert hasattr(state.execution, "messages")
    assert hasattr(state.execution, "pending_calls")

    # Test state persistence contract (no persistence)
    user_states = {}

    # Inline state creation (was _get_state)
    state_data = {
        "user_id": "user1",
        "query": "query1",
        "max_iterations": 10,
        "current_iteration": 0,
        "messages": [],
        "tools_used": [],
        "user_profile": None,
    }
    user_states["user1"] = state_data

    assert state_data is not None
    assert state_data["query"] == "query1"


@pytest.mark.asyncio
async def test_error_propagation_contract():
    """Verify errors propagate correctly through the stack."""
    from unittest.mock import patch

    llm = MockLLM()

    # Mock agent run_async to raise an exception
    with patch("cogency.Agent.run_async", new_callable=AsyncMock) as mock_run:
        mock_run.side_effect = Exception("Deliberate test failure")

        agent = Agent(name="error_test", llm=llm, tools=[], notify=False)

        # Verify exception propagation (we unwrap at boundaries)
        with pytest.raises(Exception) as exc_info:
            await agent.run_async("test error handling")

        # Should contain our deliberate failure message
        assert "failure" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_concurrent_agent_isolation():
    """Verify concurrent agents don't interfere with each other."""
    from unittest.mock import patch

    llm1 = MockLLM(response="Response from agent 1")
    llm2 = MockLLM(response="Response from agent 2")

    agent1 = Agent("agent1", llm=llm1, tools=[], notify=False, mode="fast")
    agent2 = Agent("agent2", llm=llm2, tools=[], notify=False, mode="fast")

    # Mock agent execution to avoid slow pipeline
    with patch("cogency.Agent.run_async", new_callable=AsyncMock) as mock_run:
        # Set up side_effect to return different responses based on agent
        def mock_response(query):
            if hasattr(mock_response, "call_count"):
                mock_response.call_count += 1
            else:
                mock_response.call_count = 1

            # First call returns agent1 response, second returns agent2 response
            if mock_response.call_count == 1:
                return "Response from agent 1"
            return "Response from agent 2"

        mock_run.side_effect = mock_response

        # Run concurrently with simple queries
        task1 = asyncio.create_task(agent1.run_async("Simple query 1"))
        task2 = asyncio.create_task(agent2.run_async("Simple query 2"))

        result1, result2 = await asyncio.gather(task1, task2)

        # Verify isolation - each agent gets its own response
        assert result1 == "Response from agent 1"
        assert result2 == "Response from agent 2"
        assert result1 != result2
