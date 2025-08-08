"""Storage mock fixtures for testing."""

from typing import Any, Dict

import pytest
from resilient_result import Result

from cogency.storage.backends.base import Store


class InMemoryStore(Store):
    """Fast in-memory store for testing - no file I/O overhead."""

    def __init__(self):
        self.data: Dict[str, Dict[str, Any]] = {}
        self.profiles: Dict[str, Any] = {}
        self.workspaces: Dict[str, Any] = {}

    # CANONICAL Three-Horizon Store implementation
    async def save_user_profile(self, state_key: str, profile) -> bool:
        """Save Horizon 1 - UserProfile"""
        self.profiles[state_key] = profile
        return True

    async def load_user_profile(self, state_key: str):
        """Load Horizon 1 - UserProfile"""
        return self.profiles.get(state_key)

    async def delete_user_profile(self, state_key: str) -> bool:
        """Delete user profile"""
        if state_key in self.profiles:
            del self.profiles[state_key]
            return True
        return False

    async def save_task_workspace(self, task_id: str, user_id: str, workspace) -> bool:
        """Save Horizon 2 - Workspace"""
        key = f"{task_id}:{user_id}"
        self.workspaces[key] = workspace
        return True

    async def load_task_workspace(self, task_id: str, user_id: str):
        """Load Horizon 2 - Workspace"""
        key = f"{task_id}:{user_id}"
        return self.workspaces.get(key)

    async def delete_task_workspace(self, task_id: str) -> bool:
        """Delete Horizon 2 - Workspace"""
        keys_to_delete = [k for k in self.workspaces if k.startswith(f"{task_id}:")]
        for key in keys_to_delete:
            del self.workspaces[key]
        return len(keys_to_delete) > 0

    async def list_user_workspaces(self, user_id: str):
        """List all task_ids for user's active workspaces"""
        return [k.split(":")[0] for k in self.workspaces if k.endswith(f":{user_id}")]

    # LEGACY compatibility methods
    async def save(self, key: str, data: Dict[str, Any]) -> bool:
        """Save data to memory."""
        self.data[key] = data.copy()
        return True

    async def load(self, key: str):
        """Load data from memory."""
        return self.data.get(key)

    async def delete(self, key: str) -> bool:
        """Delete data from memory."""
        if key in self.data:
            del self.data[key]
            return True
        return False

    async def list_states(self, user_id: str):
        """List all state keys."""
        return [k for k in self.data if k.startswith(f"{user_id}:")]

    def reset(self):
        """Reset store for clean test state."""
        self.data.clear()
        self.profiles.clear()
        self.workspaces.clear()


@pytest.fixture
def in_memory_store():
    """Fast in-memory store for testing."""
    store = InMemoryStore()
    yield store
    store.reset()
