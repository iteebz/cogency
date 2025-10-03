import tempfile

import pytest

from cogency.lib.storage import SQLite


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield tmp


@pytest.mark.asyncio
async def test_conversation_isolation(temp_dir):
    storage = SQLite(db_path=f"{temp_dir}/test.db")
    await storage.save_message("conv_a", "user1", "user", "Message in conv A")
    await storage.save_message("conv_b", "user1", "user", "Message in conv B")

    conv_a_messages = await storage.load_messages("conv_a", "user1")
    assert len(conv_a_messages) == 1
    assert conv_a_messages[0]["content"] == "Message in conv A"

    conv_b_messages = await storage.load_messages("conv_b", "user1")
    assert len(conv_b_messages) == 1
    assert conv_b_messages[0]["content"] == "Message in conv B"


@pytest.mark.asyncio
async def test_concurrent_writes(temp_dir):
    import asyncio

    storage = SQLite(db_path=f"{temp_dir}/test.db")

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
async def test_multi_agent_isolation(temp_dir):
    storage = SQLite(db_path=f"{temp_dir}/test.db")
    await storage.save_message("shared-channel", "agent_1", "user", "Agent 1 message")
    await storage.save_message("shared-channel", "agent_2", "user", "Agent 2 message")
    await storage.save_message("shared-channel", None, "user", "Broadcast message")

    agent1_messages = await storage.load_messages("shared-channel", "agent_1")
    assert len(agent1_messages) == 1
    assert agent1_messages[0]["content"] == "Agent 1 message"

    agent2_messages = await storage.load_messages("shared-channel", "agent_2")
    assert len(agent2_messages) == 1
    assert agent2_messages[0]["content"] == "Agent 2 message"

    all_messages = await storage.load_messages("shared-channel", None)
    assert len(all_messages) == 3


@pytest.mark.asyncio
async def test_message_ordering(temp_dir):
    storage = SQLite(db_path=f"{temp_dir}/test.db")

    await storage.save_message("conv1", "user1", "user", "First", timestamp=100)
    await storage.save_message("conv1", "user1", "respond", "Second", timestamp=200)
    await storage.save_message("conv1", "user1", "user", "Third", timestamp=300)

    messages = await storage.load_messages("conv1", "user1")

    assert len(messages) == 3
    assert messages[0]["content"] == "First"
    assert messages[1]["content"] == "Second"
    assert messages[2]["content"] == "Third"
