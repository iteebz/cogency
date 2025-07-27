"""Core memory types and data structure tests."""

import time
from datetime import UTC, datetime

from cogency.memory.core import Memory, MemoryType


def test_memory_creation():
    memory = Memory(content="test memory", memory_type=MemoryType.FACT, tags=["test"])

    assert memory.content == "test memory"
    assert memory.memory_type == MemoryType.FACT
    assert "test" in memory.tags
    assert memory.id is not None
    assert isinstance(memory.created_at, datetime)


def test_decay_score():
    memory = Memory(content="test", confidence_score=1.0)

    score = memory.decay()
    assert 0.8 < score <= 1.0


def test_access_tracking():
    memory = Memory(content="test")

    initial_count = memory.access_count
    initial_accessed = memory.last_accessed

    time.sleep(0.001)
    memory.access_count += 1
    memory.last_accessed = datetime.now(UTC)

    assert memory.access_count == initial_count + 1
    assert memory.last_accessed > initial_accessed


def test_type_enum():
    assert MemoryType.FACT
    assert MemoryType.EPISODIC
    assert MemoryType.EXPERIENCE

    fact = Memory(content="fact", memory_type=MemoryType.FACT)
    episodic = Memory(content="episodic", memory_type=MemoryType.EPISODIC)
    experience = Memory(content="experience", memory_type=MemoryType.EXPERIENCE)

    assert fact.memory_type == MemoryType.FACT
    assert episodic.memory_type == MemoryType.EPISODIC
    assert experience.memory_type == MemoryType.EXPERIENCE
