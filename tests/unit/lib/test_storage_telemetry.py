import json
import sqlite3
import uuid

import pytest

from cogency.lib.storage import DB, SQLite


@pytest.mark.asyncio
async def test_save_event(tmp_path):
    """Events are persisted with UUID primary key."""
    db_path = str(tmp_path / "test.db")
    storage = SQLite(db_path)

    event_id = await storage.save_event(
        conversation_id="conv_123", type="respond", content="test content", timestamp=1234.56
    )

    assert uuid.UUID(event_id).version == 7

    with DB.connect(db_path) as db:
        db.row_factory = sqlite3.Row
        row = db.execute("SELECT * FROM events WHERE event_id = ?", (event_id,)).fetchone()

        assert row["event_id"] == event_id
        assert row["conversation_id"] == "conv_123"
        assert row["type"] == "respond"
        assert row["content"] == "test content"
        assert row["timestamp"] == 1234.56


@pytest.mark.asyncio
async def test_save_request(tmp_path):
    """Requests are persisted with UUID primary key."""
    db_path = str(tmp_path / "test.db")
    storage = SQLite(db_path)

    messages_json = json.dumps([{"role": "user", "content": "test"}])
    response_json = json.dumps({"response": "test response"})

    request_id = await storage.save_request(
        conversation_id="conv_123",
        user_id="user_1",
        messages=messages_json,
        response=response_json,
        timestamp=1234.56,
    )

    assert uuid.UUID(request_id).version == 7

    with DB.connect(db_path) as db:
        db.row_factory = sqlite3.Row
        row = db.execute("SELECT * FROM requests WHERE request_id = ?", (request_id,)).fetchone()

        assert row["request_id"] == request_id
        assert row["conversation_id"] == "conv_123"
        assert row["user_id"] == "user_1"
        assert json.loads(row["messages"]) == [{"role": "user", "content": "test"}]
        assert json.loads(row["response"]) == {"response": "test response"}


@pytest.mark.asyncio
async def test_message_uuid_primary_key(tmp_path):
    """Messages use UUID v7 primary key instead of autoincrement."""
    db_path = str(tmp_path / "test.db")
    storage = SQLite(db_path)

    msg_id = await storage.save_message(
        conversation_id="conv_123",
        user_id="user_1",
        type="user",
        content="hello",
        timestamp=1234.56,
    )

    assert uuid.UUID(msg_id).version == 7

    with DB.connect(db_path) as db:
        db.row_factory = sqlite3.Row
        row = db.execute("SELECT * FROM messages WHERE message_id = ?", (msg_id,)).fetchone()

        assert row["message_id"] == msg_id
        assert row["conversation_id"] == "conv_123"
        assert row["type"] == "user"


@pytest.mark.asyncio
async def test_events_ordering_by_timestamp(tmp_path):
    """Events can be retrieved in chronological order."""
    db_path = str(tmp_path / "test.db")
    storage = SQLite(db_path)

    await storage.save_event("conv_1", "respond", "first", 100.0)
    await storage.save_event("conv_1", "think", "second", 200.0)
    await storage.save_event("conv_1", "respond", "third", 300.0)

    with DB.connect(db_path) as db:
        db.row_factory = sqlite3.Row
        rows = db.execute(
            "SELECT content FROM events WHERE conversation_id = ? ORDER BY timestamp", ("conv_1",)
        ).fetchall()

        assert len(rows) == 3
        assert rows[0]["content"] == "first"
        assert rows[1]["content"] == "second"
        assert rows[2]["content"] == "third"


@pytest.mark.asyncio
async def test_multiple_conversations_isolated(tmp_path):
    """Events and messages for different conversations are isolated."""
    db_path = str(tmp_path / "test.db")
    storage = SQLite(db_path)

    await storage.save_event("conv_1", "respond", "conv1_event", 100.0)
    await storage.save_event("conv_2", "respond", "conv2_event", 100.0)

    await storage.save_message("conv_1", "user_1", "user", "conv1_msg", 100.0)
    await storage.save_message("conv_2", "user_2", "user", "conv2_msg", 100.0)

    with DB.connect(db_path) as db:
        db.row_factory = sqlite3.Row

        conv1_events = db.execute(
            "SELECT content FROM events WHERE conversation_id = ?", ("conv_1",)
        ).fetchall()
        assert len(conv1_events) == 1
        assert conv1_events[0]["content"] == "conv1_event"

        conv1_messages = db.execute(
            "SELECT content FROM messages WHERE conversation_id = ?", ("conv_1",)
        ).fetchall()
        assert len(conv1_messages) == 1
        assert conv1_messages[0]["content"] == "conv1_msg"
