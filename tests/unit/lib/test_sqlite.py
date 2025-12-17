import sqlite3
import uuid

import pytest

from cogency.lib.sqlite import DB, SQLite


@pytest.mark.asyncio
async def test_conversation_isolation(tmp_path):
    storage = SQLite(db_path=tmp_path / "test.db")
    await storage.save_message("conv_a", "user1", "user", "Message in conv A")
    await storage.save_message("conv_b", "user1", "user", "Message in conv B")

    conv_a_messages = await storage.load_messages("conv_a", "user1")
    assert len(conv_a_messages) == 1
    assert conv_a_messages[0]["content"] == "Message in conv A"

    conv_b_messages = await storage.load_messages("conv_b", "user1")
    assert len(conv_b_messages) == 1
    assert conv_b_messages[0]["content"] == "Message in conv B"


@pytest.mark.asyncio
async def test_concurrent_writes(tmp_path):
    import asyncio

    storage = SQLite(db_path=tmp_path / "test.db")

    async def write_messages(conv_id, count):
        for i in range(count):
            await storage.save_message(conv_id, "user1", "user", f"Message {i}")

    await asyncio.gather(
        write_messages("conv1", 10),
        write_messages("conv2", 10),
        write_messages("conv3", 10),
    )

    conv1_messages = await storage.load_messages("conv1", "user1")
    conv2_messages = await storage.load_messages("conv2", "user1")
    conv3_messages = await storage.load_messages("conv3", "user1")

    assert len(conv1_messages) == 10
    assert len(conv2_messages) == 10
    assert len(conv3_messages) == 10


@pytest.mark.asyncio
async def test_multi_agent_isolation(tmp_path):
    storage = SQLite(db_path=tmp_path / "test.db")
    await storage.save_message("shared-channel", "agent_1", "user", "Agent 1 message")
    await storage.save_message("shared-channel", "agent_2", "user", "Agent 2 message")
    await storage.save_message("shared-channel", None, "user", "Broadcast message")  # type: ignore[arg-type]

    agent1_messages = await storage.load_messages("shared-channel", "agent_1")
    assert len(agent1_messages) == 1
    assert agent1_messages[0]["content"] == "Agent 1 message"

    agent2_messages = await storage.load_messages("shared-channel", "agent_2")
    assert len(agent2_messages) == 1
    assert agent2_messages[0]["content"] == "Agent 2 message"

    all_messages = await storage.load_messages("shared-channel", None)  # type: ignore[arg-type]
    assert len(all_messages) == 3


@pytest.mark.asyncio
async def test_message_ordering(tmp_path):
    storage = SQLite(db_path=tmp_path / "test.db")

    await storage.save_message("conv1", "user1", "user", "First", timestamp=100)
    await storage.save_message("conv1", "user1", "respond", "Second", timestamp=200)
    await storage.save_message("conv1", "user1", "user", "Third", timestamp=300)

    messages = await storage.load_messages("conv1", "user1")

    assert len(messages) == 3
    assert messages[0]["content"] == "First"
    assert messages[1]["content"] == "Second"
    assert messages[2]["content"] == "Third"


@pytest.mark.asyncio
async def test_save_load_latest_metric(tmp_path):
    """Test that we can save a metric event and retrieve the latest one."""
    db_path = tmp_path / "test.db"
    storage = SQLite(db_path=str(db_path))
    conv_id = "test_conv"
    import json
    import time

    # Save a few metric events
    metric1 = {"type": "metric", "total": {"input": 10, "output": 20}, "timestamp": time.time()}
    metric2 = {"type": "metric", "total": {"input": 15, "output": 25}, "timestamp": time.time() + 1}
    await storage.save_event(conversation_id=conv_id, type="metric", content=json.dumps(metric1))
    await storage.save_event(conversation_id=conv_id, type="metric", content=json.dumps(metric2))

    # Load the latest metric
    latest_metric = await storage.load_latest_metric(conv_id)

    # Assert that we got the latest one
    assert latest_metric is not None
    assert latest_metric["total"]["input"] == 15
    assert latest_metric["total"]["output"] == 25


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


@pytest.mark.asyncio
async def test_search_messages_excludes_current_conversation(tmp_path):
    """search_messages excludes messages from the specified conversation_id."""
    db_path = str(tmp_path / "test.db")
    storage = SQLite(db_path)

    await storage.save_message("conv_current", "user1", "user", "secret code ZEBRA123", 100.0)
    await storage.save_message("conv_past", "user1", "user", "old message about zebras", 200.0)
    await storage.save_message("conv_other", "user1", "user", "another zebra reference", 300.0)

    results = await storage.search_messages(
        query="zebra", user_id="user1", exclude_conversation_id="conv_current", limit=10
    )

    assert len(results) == 2
    conv_ids = [r.conversation_id for r in results]
    assert "conv_current" not in conv_ids
    assert "conv_past" in conv_ids
    assert "conv_other" in conv_ids


@pytest.mark.asyncio
async def test_search_messages_without_exclusion(tmp_path):
    """search_messages returns all matching messages when no exclusion specified."""
    db_path = str(tmp_path / "test.db")
    storage = SQLite(db_path)

    await storage.save_message("conv1", "user1", "user", "hello world", 100.0)
    await storage.save_message("conv2", "user1", "user", "hello there", 200.0)

    results = await storage.search_messages(
        query="hello", user_id="user1", exclude_conversation_id=None, limit=10
    )

    assert len(results) == 2


@pytest.mark.asyncio
async def test_search_messages_user_isolation(tmp_path):
    """search_messages only returns messages for the specified user."""
    db_path = str(tmp_path / "test.db")
    storage = SQLite(db_path)

    await storage.save_message("conv1", "user1", "user", "user1 secret", 100.0)
    await storage.save_message("conv2", "user2", "user", "user2 secret", 200.0)

    results = await storage.search_messages(
        query="secret", user_id="user1", exclude_conversation_id=None, limit=10
    )

    assert len(results) == 1
    assert results[0].content == "user1 secret"
