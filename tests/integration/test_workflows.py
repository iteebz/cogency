"""Integration tests for Cogency workflows."""

from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.integration
@pytest.mark.asyncio
async def test_basic_execution(agent_basic, event_monitor):
    # Mock LLM to avoid real API calls
    with patch.object(agent_basic, "llm") as mock_llm:
        mock_llm.generate = AsyncMock(return_value="I understand your request.")

        response = await agent_basic.run_async("Hello, how are you?")

        assert isinstance(response, str)
        assert len(response) > 0

        event_monitor.capture_events(agent_basic)
        event_monitor.assert_event_types(["agent"])
        event_monitor.assert_event_count("agent", min_count=1)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_with_tools(agent_with_tools, workspace, event_monitor):
    with patch.object(agent_with_tools, "llm") as mock_llm:
        mock_llm.generate = AsyncMock(return_value="Let me list the files: ls")

        response = await agent_with_tools.run_async("Show me the files in the workspace")

        assert isinstance(response, str)

        event_monitor.capture_events(agent_with_tools)
        event_monitor.assert_event_types(["agent", "tool"])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_memory_persistence(clean_env, memory_session, event_monitor):
    agent1 = memory_session.create_agent(clean_env)

    # Mock the llm provider more comprehensively for memory agents
    with patch("cogency.agents.reason") as mock_reason:
        mock_reason.return_value = {"response": "I'll remember that you like Python programming."}

        response1 = await agent1.run_async("Remember that I like Python programming")
        assert "remember" in response1.lower() or "python" in response1.lower()

    agent2 = memory_session.create_agent(clean_env)

    with patch("cogency.agents.reason") as mock_reason:
        mock_reason.return_value = {"response": "You mentioned you like Python programming."}

        await agent2.run_async("What do you know about my preferences?")

        memory_session.verify_memory_persistence()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_workflow(agent_full, workspace, event_monitor, performance_baseline):
    query = "Analyze the files in my workspace and remember my project structure"

    responses = [
        "I'll analyze your workspace files.",
        "I found Python and JSON files. Let me read them.",
        "I've analyzed your project structure and will remember it.",
    ]

    with patch.object(agent_full, "llm") as mock_llm:
        mock_llm.generate = AsyncMock(side_effect=responses)

        response = await performance_baseline.measure_async(
            "full_workflow", agent_full.run_async, query
        )

        assert isinstance(response, str)
        assert len(response) > 0

        event_monitor.capture_events(agent_full)
        event_monitor.assert_event_types(["agent", "memory", "tool"])

        performance_baseline.assert_performance("full_workflow", max_seconds=5.0)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_error_recovery(agent_with_tools, workspace):
    with patch.object(agent_with_tools, "llm") as mock_llm:
        mock_llm.generate = AsyncMock(return_value="Let me try: invalid_command --bad-flag")

        response = await agent_with_tools.run_async("Run an invalid command")

        assert isinstance(response, str)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tool_chain(agent_with_tools, workspace, tool_chain):
    responses = [
        "I'll create a file first: echo 'test' > new_file.txt",
        "Now I'll list the files: ls -la",
        "Finally I'll read the file: cat new_file.txt",
    ]

    with patch.object(agent_with_tools, "llm") as mock_llm:
        mock_llm.generate = AsyncMock(side_effect=responses)

        await agent_with_tools.run_async("Create a test file, list directory, then read the file")

        expected_operations = [
            {"type": "shell"},
            {"type": "file"},
        ]
        tool_chain.verify_chain(expected_operations)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_event_filtering(agent_full, workspace):
    with patch.object(agent_full, "llm") as mock_llm:
        mock_llm.generate = AsyncMock(return_value="Task completed successfully.")

        await agent_full.run_async("Simple test query")

        all_events = agent_full.logs()
        agent_events = agent_full.logs(type="agent")
        recent_events = agent_full.logs(last=5)
        agent_full.logs(errors_only=True)

        assert len(all_events) >= len(agent_events)
        assert len(recent_events) <= 5
        assert len(agent_events) > 0

        for event in agent_events:
            assert event.get("type") == "agent"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_event_capture(agent_full, workspace, event_monitor):
    with patch.object(agent_full, "llm") as mock_llm:
        mock_llm.generate = AsyncMock(return_value="Complex workflow completed.")

        await agent_full.run_async("Perform complex operations with memory and tools")

        events = event_monitor.capture_events(agent_full)

        expected_event_types = ["agent", "memory", "tool"]
        event_monitor.assert_event_types(expected_event_types)

        for event in events:
            assert "type" in event
            assert "timestamp" in event or "time" in event


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_performance_baseline(agent_basic, performance_baseline):
    with patch.object(agent_basic, "llm") as mock_llm:
        mock_llm.generate = AsyncMock(return_value="Quick response.")

        await performance_baseline.measure_async(
            "basic_execution", agent_basic.run_async, "Simple query"
        )

        performance_baseline.assert_performance("basic_execution", max_seconds=1.0)


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_memory_performance(agent_with_memory, performance_baseline):
    with patch.object(agent_with_memory, "llm") as mock_llm:
        mock_llm.generate = AsyncMock(return_value="Memory operation completed.")

        await performance_baseline.measure_async(
            "memory_execution", agent_with_memory.run_async, "Remember this information"
        )

        performance_baseline.assert_performance("memory_execution", max_seconds=2.0)


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_tool_performance(agent_with_tools, workspace, performance_baseline):
    with patch.object(agent_with_tools, "llm") as mock_llm:
        mock_llm.generate = AsyncMock(return_value="Tool operation completed.")

        await performance_baseline.measure_async(
            "tool_execution", agent_with_tools.run_async, "List files in workspace"
        )

        performance_baseline.assert_performance("tool_execution", max_seconds=3.0)
