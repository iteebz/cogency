import tempfile
from pathlib import Path

import pytest

from cogency.lib.paths import Paths, get_cogency_dir
from cogency.lib.storage import SQLite


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield tmp


@pytest.mark.asyncio
async def test_user_isolation(temp_dir):
    storage = SQLite(temp_dir)
    await storage.save_message("conv1", "user_A", "user", "Message from A")
    await storage.save_message("conv1", "user_B", "user", "Message from B")

    user_a_messages = await storage.load_messages("conv1", "user_A")
    assert len(user_a_messages) == 1
    assert user_a_messages[0]["content"] == "Message from A"

    user_b_messages = await storage.load_messages("conv1", "user_B")
    assert len(user_b_messages) == 1
    assert user_b_messages[0]["content"] == "Message from B"


@pytest.mark.asyncio
async def test_concurrent_writes(temp_dir):
    import asyncio

    storage = SQLite(temp_dir)

    async def write_messages(user_id, count):
        for i in range(count):
            await storage.save_message("conv1", user_id, "user", f"Message {i}")

    await asyncio.gather(
        write_messages("user1", 10),
        write_messages("user2", 10),
        write_messages("user3", 10),
    )

    user1_messages = await storage.load_messages("conv1", "user1")
    user2_messages = await storage.load_messages("conv1", "user2")
    user3_messages = await storage.load_messages("conv1", "user3")

    assert len(user1_messages) == 10
    assert len(user2_messages) == 10
    assert len(user3_messages) == 10


@pytest.mark.asyncio
async def test_message_ordering(temp_dir):
    storage = SQLite(temp_dir)

    await storage.save_message("conv1", "user1", "user", "First", timestamp=100)
    await storage.save_message("conv1", "user1", "respond", "Second", timestamp=200)
    await storage.save_message("conv1", "user1", "user", "Third", timestamp=300)

    messages = await storage.load_messages("conv1", "user1")

    assert len(messages) == 3
    assert messages[0]["content"] == "First"
    assert messages[1]["content"] == "Second"
    assert messages[2]["content"] == "Third"