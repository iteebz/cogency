"""Integration tests for Agent coordination with React and Context."""

from unittest.mock import AsyncMock, patch

import pytest

from cogency import Agent
from cogency.lib.result import Ok


@pytest.mark.asyncio
async def test_streaming_preserves_sync_behavior(mock_llm):
    """Verify streaming doesn't break synchronous execution."""
    # Use canonical mock fixture
    xml_response = """<thinking>
Processing streaming test.
</thinking>

<response>
Test response
</response>"""
    mock_llm.generate = AsyncMock(return_value=Ok(xml_response))

    with patch("cogency.core.agent.create_llm", return_value=mock_llm):
        with patch("cogency.core.react.context") as mock_context:
            mock_context.assemble.return_value = "context"
            agent = Agent(tools=[])

            # Test synchronous call still works
            sync_result = await agent("Test query", user_id="sync_test")
            assert "Test response" in sync_result.response
            assert sync_result.conversation_id == "sync_test"

            # Test streaming works
            stream_events = []
            async for event in agent.stream("Test query", user_id="stream_test"):
                stream_events.append(event)

            # Both should complete successfully
            assert len(stream_events) > 0
            complete_events = [e for e in stream_events if e["type"] == "complete"]
            assert len(complete_events) == 1
            assert "Test response" in complete_events[0]["answer"]


@pytest.mark.asyncio
async def test_streaming_context_assembly(mock_llm):
    """Test streaming properly assembles context like sync version."""
    xml_response = """<thinking>
Context assembly test.
</thinking>

<response>
Done
</response>"""
    mock_llm.generate = AsyncMock(return_value=Ok(xml_response))

    with patch("cogency.core.agent.create_llm", return_value=mock_llm):
        with patch("cogency.core.react.context") as mock_context:
            mock_context.assemble.return_value = "assembled context"
            agent = Agent(tools=[])
            events = []

            async for event in agent.stream("Test", user_id="context_test"):
                events.append(event)

            # Context should be called with current signature
            assert mock_context.assemble.called
            call_args = mock_context.assemble.call_args[0]
            assert call_args[0] == "Test"  # query
            assert call_args[1] == "context_test"  # user_id

            # Context length should be reported in event
            context_events = [e for e in events if e["type"] == "context"]
            assert len(context_events) == 1
            assert context_events[0]["length"] == len("assembled context")


@pytest.mark.asyncio
async def test_streaming_conversation_id_consistency(mock_llm):
    """Verify streaming conversation_id follows same pattern as sync."""
    xml_response = """<thinking>
Testing consistency.
</thinking>

<response>
Consistent
</response>"""
    mock_llm.generate = AsyncMock(return_value=Ok(xml_response))

    with patch("cogency.core.agent.create_llm", return_value=mock_llm):
        with patch("cogency.core.react.context") as mock_context:
            mock_context.assemble.return_value = "context"
            agent = Agent(tools=[])

            # Get sync conversation ID pattern
            sync_result = await agent("Test", user_id="user123")
            sync_conv_id = sync_result.conversation_id

            # Get streaming conversation ID
            stream_events = []
            async for event in agent.stream("Test", user_id="user123"):
                stream_events.append(event)

            complete_events = [e for e in stream_events if e["type"] == "complete"]
            stream_conv_id = complete_events[0]["conversation_id"]

            # Both should use user_id as conversation_id when not specified
            assert sync_conv_id == "user123"
            assert stream_conv_id == "user123"

            # Both use same conversation ID format
