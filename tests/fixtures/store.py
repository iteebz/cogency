"""Storage mock fixtures for testing."""

from typing import Any, Dict

import pytest
from resilient_result import Result

from cogency.persist.store.base import Store


class InMemoryStore(Store):
    """Fast in-memory store for testing - no file I/O overhead."""

    def __init__(self):
        self.data: Dict[str, Dict[str, Any]] = {}

    async def save(self, key: str, data: Dict[str, Any]) -> Result:
        """Save data to memory."""
        self.data[key] = data.copy()
        return Result.ok(None)

    async def load(self, key: str) -> Result:
        """Load data from memory."""
        if key in self.data:
            return Result.ok(self.data[key].copy())
        return Result.fail(f"Key not found: {key}")

    async def delete(self, key: str) -> Result:
        """Delete data from memory."""
        if key in self.data:
            del self.data[key]
            return Result.ok(None)
        return Result.fail(f"Key not found: {key}")

    async def list_keys(self) -> Result:
        """List all keys."""
        return Result.ok(list(self.data.keys()))

    async def list_states(self) -> Result:
        """List all state keys (for Store interface compliance)."""
        return Result.ok([k for k in self.data if k.startswith("state_")])

    def reset(self):
        """Reset store for clean test state."""
        self.data.clear()


@pytest.fixture
def in_memory_store():
    """Fast in-memory store for testing."""
    store = InMemoryStore()
    yield store
    store.reset()
