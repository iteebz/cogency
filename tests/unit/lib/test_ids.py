import time
import uuid

import pytest

from cogency.lib.ids import uuid7


@pytest.mark.asyncio
async def test_generation():
    """UUID v7 generates time-ordered unique IDs."""
    id1 = uuid7()
    id2 = uuid7()

    assert id1 != id2
    u1 = uuid.UUID(id1)
    u2 = uuid.UUID(id2)

    assert u1.version == 7
    assert u2.version == 7

    # RFC 9562: variant must be 0b10
    assert u1.variant == uuid.RFC_4122
    assert u2.variant == uuid.RFC_4122

    # Time-ordered: later IDs should sort after earlier ones
    assert id1 < id2


@pytest.mark.asyncio
async def test_timestamp_ordering():
    """UUID v7 embeds millisecond timestamp for chronological sorting."""
    before = int(time.time() * 1000)
    id1 = uuid7()
    time.sleep(0.01)
    id2 = uuid7()
    after = int(time.time() * 1000)

    # Extract timestamp from UUID v7 (first 48 bits)
    u1 = uuid.UUID(id1)
    u2 = uuid.UUID(id2)

    ts1_ms = (u1.int >> 80) & 0xFFFFFFFFFFFF
    ts2_ms = (u2.int >> 80) & 0xFFFFFFFFFFFF

    # Timestamps should be in valid range
    assert before <= ts1_ms <= after
    assert before <= ts2_ms <= after

    # Second UUID should have later timestamp
    assert ts2_ms >= ts1_ms


@pytest.mark.asyncio
async def test_uniqueness():
    """UUID v7 generates unique IDs even in tight loop."""
    ids = [uuid7() for _ in range(1000)]
    assert len(ids) == len(set(ids))
