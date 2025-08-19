"""Integration tests for Agent coordination with React and Context."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from cogency import Agent
from cogency.lib.result import Ok


@pytest.mark.asyncio
async def test_streaming_preserves_sync_behavior():
    """Verify streaming doesn't break synchronous execution."""
    # Mock LLM that returns final answer
    mock_llm = Mock()
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
            with patch("cogency.core.react.persist") as mock_persist:
                agent = Agent(tools=[])

                # Test synchronous call still works
                sync_result = await agent("Test query", user_id="sync_test")
                assert "Test response" in sync_result.response
                assert sync_result.conversation_id.startswith("sync_test_")

                # Test streaming works
                stream_events = []
                async for event in agent.stream("Test query", user_id="stream_test"):
                    stream_events.append(event)

                # Both should complete successfully
                assert len(stream_events) > 0
                complete_events = [e for e in stream_events if e["type"] == "complete"]
                assert len(complete_events) == 1
                assert "Test response" in complete_events[0]["answer"]

                # Both should have called persist
                assert mock_persist.call_count >= 1


@pytest.mark.asyncio
async def test_streaming_context_assembly():
    """Test streaming properly assembles context like sync version."""
    mock_llm = Mock()
    xml_response = """<thinking>
Context assembly test.
</thinking>

<response>
Done
</response>"""
    mock_llm.generate = AsyncMock(return_value=Ok(xml_response))

    with patch("cogency.core.agent.create_llm", return_value=mock_llm):
        with patch("cogency.core.react.context") as mock_context:
            with patch("cogency.core.react.persist"):
                mock_context.assemble.return_value = "assembled context"
                agent = Agent(tools=[])
                events = []

                async for event in agent.stream("Test", user_id="context_test"):
                    events.append(event)

                # Context should be called with same parameters as sync version
                mock_context.assemble.assert_called_with("Test", "context_test", [], {}, 0)

                # Context length should be reported in event
                context_events = [e for e in events if e["type"] == "context"]
                assert len(context_events) == 1
                assert context_events[0]["length"] == len("assembled context")


@pytest.mark.asyncio
async def test_streaming_conversation_id_consistency():
    """Verify streaming conversation_id follows same pattern as sync."""
    mock_llm = Mock()
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
            with patch("cogency.core.react.persist"):
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

                # Both should follow user_id_timestamp pattern
                assert sync_conv_id.startswith("user123_")
                assert stream_conv_id.startswith("user123_")
                assert len(sync_conv_id.split("_")) == 2
                assert len(stream_conv_id.split("_")) == 2

                # Timestamps should be integers
                sync_timestamp = sync_conv_id.split("_")[1]
                stream_timestamp = stream_conv_id.split("_")[1]
                assert sync_timestamp.isdigit()
                assert stream_timestamp.isdigit()
