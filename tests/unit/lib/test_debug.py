import json

from cogency.lib.debug import log_response


def test_creates_file_and_logs_json(tmp_path, monkeypatch):
    """
    Test that log_response creates a .jsonl file and logs valid JSON content.
    """
    monkeypatch.chdir(tmp_path)
    conversation_id = "test_conversation_123"
    model = "test_model"
    response = "This is a test response."

    log_response(conversation_id, model, response)

    log_file = tmp_path / ".cogency/debug" / f"{conversation_id}.jsonl"
    assert log_file.exists()

    with open(log_file) as f:
        line = f.readline()
        entry = json.loads(line)

    assert "request_id" in entry
    assert "timestamp" in entry
    assert entry["model"] == model
    assert entry["response"] == response


def test_appends_to_existing_file(tmp_path, monkeypatch):
    """
    Test that log_response appends new entries to an existing .jsonl file.
    """
    monkeypatch.chdir(tmp_path)
    conversation_id = "test_conversation_456"
    model = "test_model_2"
    response1 = "First response."
    response2 = "Second response."

    log_response(conversation_id, model, response1)
    log_response(conversation_id, model, response2)

    log_file = tmp_path / ".cogency/debug" / f"{conversation_id}.jsonl"
    assert log_file.exists()

    with open(log_file) as f:
        lines = f.readlines()

    assert len(lines) == 2
    entry1 = json.loads(lines[0])
    entry2 = json.loads(lines[1])

    assert entry1["response"] == response1
    assert entry2["response"] == response2


def test_handles_empty_response(tmp_path, monkeypatch):
    """
    Test that log_response does not log an empty response.
    """
    monkeypatch.chdir(tmp_path)
    conversation_id = "test_conversation_789"
    model = "test_model_3"
    response = ""

    log_response(conversation_id, model, response)

    log_file = tmp_path / ".cogency/debug" / f"{conversation_id}.jsonl"
    assert not log_file.exists()
