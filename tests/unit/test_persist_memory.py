"""Memory persistence integration tests."""

from unittest.mock import AsyncMock

import pytest

from cogency.memory import Memory
from cogency.persist.store.filesystem import Filesystem


@pytest.mark.asyncio
async def test_memory_save_load():
    """Test memory save and load functionality."""
    # Mock LLM
    llm = AsyncMock()

    # Create filesystem store in temp directory
    store = Filesystem(base_dir=".cogency/memory")

    # Create memory instance
    memory = Memory(llm=llm, store=store, user_id="test_user")

    # Set some memory data
    memory.recent = "[HUMAN] Hello world\n[AGENT] How can I help?"
    memory.impression = "User is friendly and needs assistance"

    # Save memory
    success = await memory.save()
    assert success is True

    # Create new memory instance and load
    memory2 = Memory(llm=llm, store=store, user_id="test_user")
    success = await memory2.load()
    assert success is True

    # Verify data persistence
    assert memory2.recent == "[HUMAN] Hello world\n[AGENT] How can I help?"
    assert memory2.impression == "User is friendly and needs assistance"


@pytest.mark.asyncio
async def test_memory_load_empty():
    """Test loading memory when no data exists."""
    llm = AsyncMock()
    store = Filesystem(base_dir=".cogency/memory")

    memory = Memory(llm=llm, store=store, user_id="nonexistent_user")
    success = await memory.load()

    assert success is False
    assert memory.recent == ""
    assert memory.impression == ""


@pytest.mark.asyncio
async def test_memory_save_without_store():
    """Test save/load behavior when no store is provided."""
    llm = AsyncMock()
    memory = Memory(llm=llm)  # No store provided

    memory.recent = "Some data"
    memory.impression = "Some impression"

    # Should return False when no store
    success = await memory.save()
    assert success is False

    success = await memory.load()
    assert success is False


@pytest.mark.asyncio
async def test_auto_save_on_synthesis():
    """Test that memory auto-saves after synthesis."""
    llm = AsyncMock()
    llm.run.return_value = AsyncMock(success=True, data="Synthesized impression")

    store = AsyncMock()
    store.save = AsyncMock(return_value=True)

    memory = Memory(llm=llm, store=store, user_id="test_user")
    memory.recent = "Some interactions over threshold"

    # Trigger synthesis
    await memory._synthesize()

    # Verify auto-save was called
    store.save.assert_called_once()

    # Verify the memory key format
    call_args = store.save.call_args
    memory_key = call_args[0][0]
    assert memory_key == "memory:test_user"


@pytest.mark.asyncio
async def test_user_scoped_memory():
    """Test that different users have separate memory storage."""
    llm = AsyncMock()
    store = Filesystem(base_dir=".cogency/memory")

    # Create memory for user1
    memory1 = Memory(llm=llm, store=store, user_id="user1")
    memory1.recent = "User1 data"
    memory1.impression = "User1 impression"
    await memory1.save()

    # Create memory for user2
    memory2 = Memory(llm=llm, store=store, user_id="user2")
    memory2.recent = "User2 data"
    memory2.impression = "User2 impression"
    await memory2.save()

    # Load user1 memory into new instance
    memory1_reload = Memory(llm=llm, store=store, user_id="user1")
    await memory1_reload.load()

    # Verify user1 data is isolated
    assert memory1_reload.recent == "User1 data"
    assert memory1_reload.impression == "User1 impression"

    # Load user2 memory into new instance
    memory2_reload = Memory(llm=llm, store=store, user_id="user2")
    await memory2_reload.load()

    # Verify user2 data is isolated
    assert memory2_reload.recent == "User2 data"
    assert memory2_reload.impression == "User2 impression"
