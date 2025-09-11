"""Error boundary integration tests - failure recovery across components."""

import tempfile
from unittest.mock import Mock, patch

import pytest

from cogency import Agent
from cogency.lib.storage import SQLite, load_messages


@pytest.fixture
def temp_storage():
    """Temporary storage for isolated tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.mark.asyncio
async def test_llm_failure_recovery(temp_storage):
    """Agent recovers gracefully from LLM failures."""

    # Mock LLM that fails then succeeds
    call_count = 0
    mock_llm = Mock()

    async def mock_failing_stream(*args, **kwargs):
        nonlocal call_count
        call_count += 1

        if call_count == 1:
            # First call fails
            raise Exception("LLM API error")
        else:
            # Second call succeeds
            yield "§THINK"
            yield "Now working properly"
            yield "§RESPOND"
            yield "Success after retry"
            yield "§EXECUTE"

    mock_llm.stream.side_effect = mock_failing_stream
    mock_llm.resumable = False

    with patch("cogency.lib.llms.Gemini", return_value=mock_llm):
        agent = Agent(llm="gemini")

        # First call should fail gracefully
        with pytest.raises(RuntimeError, match="Agent execution failed"):
            await agent("Test message", user_id="user1")

        # Storage should still be consistent
        messages = load_messages("user1_session")
        # Should have user message even if agent failed
        user_messages = [m for m in messages if m["type"] == "user"]
        assert len(user_messages) >= 1

        # Second call should succeed
        response = await agent("Test message again", user_id="user1")
        assert "Success after retry" in response


@pytest.mark.asyncio
async def test_storage_failure_resilience(temp_storage):
    """Agent continues working despite storage failures."""

    mock_llm = Mock()

    async def mock_stream(*args, **kwargs):
        yield "§THINK"
        yield "Responding despite storage issues"
        yield "§RESPOND"
        yield "I can still respond even if storage fails"
        yield "§EXECUTE"

    mock_llm.stream.return_value = mock_stream()
    mock_llm.resumable = False

    with patch("cogency.lib.llms.Gemini", return_value=mock_llm):
        with patch("cogency.lib.storage.save_message", side_effect=Exception("Storage error")):
            agent = Agent(llm="gemini")

            # Should still get response despite storage failure
            response = await agent("Test message", user_id="user1")
            assert isinstance(response, str)
            assert len(response) > 0


@pytest.mark.asyncio
async def test_tool_failure_chain_recovery(temp_storage):
    """Agent handles tool failures in multi-tool workflows."""

    mock_llm = Mock()

    async def mock_tool_failure_stream(*args, **kwargs):
        yield "§THINK"
        yield "Trying to read file then write result"
        yield "§CALLS"
        yield '[{"name": "read", "args": {"file_path": "nonexistent.txt"}}]'  # This will fail
        yield "§EXECUTE"
        yield "§THINK"
        yield "First tool failed, but I can continue"
        yield "§CALLS"
        yield '[{"name": "write", "args": {"file_path": "output.txt", "content": "Handled failure gracefully"}}]'
        yield "§EXECUTE"
        yield "§RESPOND"
        yield "Despite the first tool failing, I completed what I could"
        yield "§EXECUTE"

    mock_llm.stream.return_value = mock_tool_failure_stream()
    mock_llm.resumable = False

    with patch("cogency.lib.llms.Gemini", return_value=mock_llm):
        agent = Agent(llm="gemini", sandbox=True)

        # Agent should handle partial tool failure gracefully
        response = await agent("Read nonexistent.txt and write a summary", user_id="user1")
        assert isinstance(response, str)
        assert "completed" in response.lower()


@pytest.mark.asyncio
async def test_parser_error_recovery(temp_storage):
    """Stream parser handles malformed input gracefully."""

    mock_llm = Mock()

    async def mock_malformed_stream(*args, **kwargs):
        yield "§THINK"
        yield "Starting normally"
        yield "§CALLS"
        yield '{"invalid": json malformed'  # Malformed JSON
        yield "§RESPOND"
        yield "Continuing after parse error"
        yield "§EXECUTE"

    mock_llm.stream.return_value = mock_malformed_stream()
    mock_llm.resumable = False

    with patch("cogency.lib.llms.Gemini", return_value=mock_llm):
        agent = Agent(llm="gemini")

        # Should handle malformed JSON gracefully
        response = await agent("Test malformed JSON handling", user_id="user1")
        assert isinstance(response, str)
        # Should get response despite JSON parsing error
        assert len(response) > 0


@pytest.mark.asyncio
async def test_concurrent_error_isolation(temp_storage):
    """Errors in one user session don't affect others."""

    # Mock LLM that fails for user1 but works for user2
    mock_llm = Mock()

    def mock_stream_factory(*args, **kwargs):
        # Check if this is for user1 or user2 based on call pattern
        async def failing_stream():
            yield "§THINK"
            raise Exception("Specific user failure")

        async def working_stream():
            yield "§THINK"
            yield "Working normally"
            yield "§RESPOND"
            yield "Success for this user"
            yield "§END"

        return failing_stream() if mock_llm.stream.call_count == 1 else working_stream()

    mock_llm.stream.side_effect = mock_stream_factory
    mock_llm.resumable = False

    with patch("cogency.lib.llms.Gemini", return_value=mock_llm):
        storage = SQLite(temp_storage)
        agent = Agent(llm="gemini", storage=storage)

        # User 1 fails
        with pytest.raises(RuntimeError):
            await agent("This will fail", user_id="user1")

        # User 2 should still work
        response = await agent("This should work", user_id="user2")
        assert "Success for this user" in response

        # Verify storage isolation - user2's session unaffected
        user2_messages = load_messages("user2_session", base_dir=temp_storage)
        user_messages = [m for m in user2_messages if m["type"] == "user"]
        assert len(user_messages) >= 1
        assert "This should work" in user_messages[0]["content"]


@pytest.mark.asyncio
async def test_memory_error_graceful_degradation(temp_storage):
    """Memory system failures degrade gracefully without breaking agent."""

    mock_llm = Mock()

    async def mock_stream(*args, **kwargs):
        yield "§THINK"
        yield "Responding without memory context"
        yield "§RESPOND"
        yield "I can still respond even without memory"
        yield "§EXECUTE"

    mock_llm.stream.return_value = mock_stream()
    mock_llm.resumable = False

    # Mock profile operations to fail
    with patch("cogency.lib.llms.Gemini", return_value=mock_llm):
        with patch("cogency.context.profile.load_profile", side_effect=Exception("Memory error")):
            agent = Agent(llm="gemini", profile=True)

            # Should still work despite memory system failure
            response = await agent("Test message", user_id="user1")
            assert isinstance(response, str)
            assert len(response) > 0
