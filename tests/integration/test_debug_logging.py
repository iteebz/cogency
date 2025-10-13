import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cogency.core import replay, resume
from cogency.core.config import Config
from cogency.core.protocols import LLM
from cogency.lib.storage import SQLite


# Mock for replay (HTTP streaming) integration tests
class MockReplayLLM:
    def __init__(self, responses):
        self.responses = responses
        self.http_model = "mock-replay-model"
        self.resumable = False

    async def stream(self, messages):
        for response_chunk in self.responses:
            yield f"§respond: {response_chunk}"
        yield "§end"


@pytest.fixture
def mock_replay_llm():
    def _factory(responses):
        return MockReplayLLM(responses)

    return _factory


# Mock for resume (WebSocket) integration tests
class MockResumeLLM(LLM):
    def __init__(self, connect_response, send_responses):
        self.connect_response = connect_response
        self.send_responses = send_responses
        self.http_model = "mock-resume-model"
        self.resumable = True

    async def connect(self, messages):
        mock_session = MagicMock()
        send_responses_iter = iter(self.send_responses)

        async def send_generator_func(content):
            try:
                responses = next(send_responses_iter)
                for response_chunk in responses:
                    if isinstance(response_chunk, dict):
                        yield f"§{response_chunk['type']}: {json.dumps(response_chunk['content'])}"
                    else:
                        yield f"§respond: {response_chunk}"
                yield "§end"
            except StopIteration:
                yield "§end"

        mock_session.send = AsyncMock(side_effect=lambda content: send_generator_func(content))
        mock_session.close = AsyncMock()
        return mock_session

    async def stream(self, messages):
        raise NotImplementedError("stream() should not be called in resume mode tests")


@pytest.fixture
def mock_resume_llm():
    def _factory(connect_response, send_responses):
        return MockResumeLLM(connect_response, send_responses)

    return _factory


# Helper to read and parse debug logs
def read_debug_log(tmp_path, conversation_id):
    debug_dir = tmp_path / ".cogency/debug"
    log_file = debug_dir / f"{conversation_id}.jsonl"
    if not log_file.exists():
        return []
    with open(log_file) as f:
        return [json.loads(line) for line in f]


@pytest.mark.asyncio
async def test_replay_debug_logging_enabled(tmp_path, mock_replay_llm, monkeypatch):
    """
    Test that debug logs are created for replay mode when enabled.
    """
    conversation_id = "replay_debug_enabled_conv"
    user_id = "test_user"
    mock_responses = ["Hello from replay.", "How can I help?"]

    # The original test had a bug where mock_responses was defined but not used.
    # The generic mock_llm was used instead. This is now corrected.
    llm = mock_replay_llm(mock_responses)

    config = Config(
        llm=llm,
        storage=SQLite(db_path=str(tmp_path / "test.db")),
        debug=True,
        tools=[],
    )

    monkeypatch.chdir(tmp_path)

    # Run replay stream
    async for _ in replay.stream(
        query="test",
        user_id=user_id,
        conversation_id=conversation_id,
        config=config,
    ):
        pass

    logs = read_debug_log(tmp_path, conversation_id)
    assert len(logs) == 1
    log_entry = logs[0]
    assert log_entry["model"] == llm.http_model
    assert log_entry["response"] == "".join(mock_responses)
    assert "request_id" in log_entry
    assert "timestamp" in log_entry


@pytest.mark.asyncio
async def test_replay_debug_logging_disabled(tmp_path, mock_replay_llm):
    """
    Test that debug logs are NOT created for replay mode when disabled.
    """
    conversation_id = "replay_debug_disabled_conv"
    user_id = "test_user"
    mock_responses = ["Hello from replay."]
    llm = mock_replay_llm(mock_responses)
    config = Config(
        llm=llm,
        storage=SQLite(db_path=str(tmp_path / "test.db")),
        debug=False,  # Debug disabled
        tools=[],
    )

    # Run replay stream
    logs = read_debug_log(tmp_path, conversation_id)
    assert len(logs) == 0
    assert not (tmp_path / ".cogency/debug" / f"{conversation_id}.jsonl").exists()


@pytest.mark.asyncio
async def test_resume_debug_logging_enabled(tmp_path, mock_resume_llm, monkeypatch):
    """
    Test that debug logs are created for resume mode when enabled.
    """
    conversation_id = "resume_debug_enabled_conv"
    user_id = "test_user"
    send_responses = [
        [{"type": "respond", "content": "First part."}],
    ]
    llm = mock_resume_llm(None, send_responses)

    config = Config(
        llm=llm,
        storage=SQLite(db_path=str(tmp_path / "test.db")),
        debug=True,
        tools=[],
    )

    monkeypatch.chdir(tmp_path)

    # Mock context.assemble to return a simple message list
    with patch("cogency.context.assemble", new_callable=AsyncMock) as mock_assemble:
        mock_assemble.return_value = [{"role": "user", "content": "initial query"}]
        # Run resume stream
        async for _ in resume.stream(
            query="test",
            user_id=user_id,
            conversation_id=conversation_id,
            config=config,
        ):
            pass

    logs = read_debug_log(tmp_path, conversation_id)
    assert len(logs) == 1

    log_entry = logs[0]
    assert log_entry["model"] == llm.http_model
    assert log_entry["response"] == '"First part."'
    assert "request_id" in log_entry


@pytest.mark.asyncio
async def test_resume_debug_logging_disabled(tmp_path, mock_resume_llm):
    """
    Test that debug logs are NOT created for resume mode when disabled.
    """
    conversation_id = "resume_debug_disabled_conv"
    user_id = "test_user"
    connect_response = [{"type": "respond", "content": "Connected."}]
    send_responses = [[{"type": "respond", "content": "First part."}]]
    llm = mock_resume_llm(connect_response, send_responses)

    config = Config(
        llm=llm,
        storage=SQLite(db_path=str(tmp_path / "test.db")),
        debug=False,  # Debug disabled
        tools=[],
    )

    debug_dir = tmp_path / ".cogency/debug"
    with patch("cogency.context.assemble", new_callable=AsyncMock) as mock_assemble:
        mock_assemble.return_value = [{"role": "user", "content": "initial query"}]
        # Run resume stream
        async for _ in resume.stream(
            query="test",
            user_id=user_id,
            conversation_id=conversation_id,
            config=config,
        ):
            pass

    logs = read_debug_log(debug_dir, conversation_id)
    assert len(logs) == 0
    assert not (tmp_path / ".cogency/debug" / f"{conversation_id}.jsonl").exists()
