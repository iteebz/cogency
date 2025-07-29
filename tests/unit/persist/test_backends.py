"""Unit tests for state persistence backends."""

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from cogency.persist import FilesystemBackend
from cogency.state import State


class TestFilesystemBackend:
    """Test file-based state persistence."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield tmp_dir

    @pytest.fixture
    def backend(self, temp_dir):
        """Create backend with temp directory."""
        return FilesystemBackend(base_dir=temp_dir)

    @pytest.fixture
    def sample_state(self):
        """Create sample state for testing."""
        state = State(query="test query", user_id="test_user")
        state.add_message("user", "Hello")
        state.add_message("assistant", "Hi there")
        return state

    @pytest.fixture
    def sample_metadata(self):
        """Sample metadata for testing."""
        return {
            "llm_provider": "openai",
            "llm_model": "gpt-4",
            "tools_count": 3,
            "memory_backend": "filesystem",
        }

    @pytest.mark.asyncio
    async def test_save_and_load_state(self, backend, sample_state, sample_metadata):
        """Test basic save and load operations."""
        state_key = "test_user:session1"

        # Save state
        success = await backend.save(state_key, sample_state, sample_metadata)
        assert success is True

        # Load state
        loaded_data = await backend.load_state(state_key)
        assert loaded_data is not None
        assert loaded_data["metadata"] == sample_metadata
        assert loaded_data["state"]["query"] == "test query"
        assert loaded_data["state"]["user_id"] == "test_user"
        assert len(loaded_data["state"]["messages"]) == 2

    @pytest.mark.asyncio
    async def test_load_nonexistent_state(self, backend):
        """Test loading state that doesn't exist."""
        loaded_data = await backend.load_state("nonexistent_key")
        assert loaded_data is None

    @pytest.mark.asyncio
    async def test_delete_state(self, backend, sample_state, sample_metadata):
        """Test state deletion."""
        state_key = "test_user:session1"

        # Save first
        await backend.save(state_key, sample_state, sample_metadata)

        # Verify exists
        loaded_data = await backend.load_state(state_key)
        assert loaded_data is not None

        # Delete
        success = await backend.delete_state(state_key)
        assert success is True

        # Verify deleted
        loaded_data = await backend.load_state(state_key)
        assert loaded_data is None

    @pytest.mark.asyncio
    async def test_process_isolation(self, temp_dir):
        """Test that different process IDs create separate files."""
        backend1 = FilesystemBackend(base_dir=temp_dir)
        backend2 = FilesystemBackend(base_dir=temp_dir)

        # Different backends should have different process IDs
        assert backend1.process_id != backend2.process_id

        state_key = "test_user:session1"
        sample_state = State(query="test", user_id="test_user")
        sample_metadata = {"test": "data"}

        # Save with backend1
        await backend1.save(state_key, sample_state, sample_metadata)

        # Backend2 shouldn't see backend1's state
        loaded_data = await backend2.load_state(state_key)
        assert loaded_data is None

        # But backend1 can still load its own state
        loaded_data = await backend1.load_state(state_key)
        assert loaded_data is not None

    @pytest.mark.asyncio
    async def test_schema_version_validation(self, backend, sample_state, sample_metadata):
        """Test schema version validation."""
        state_key = "test_user:session1"

        # Save state normally
        await backend.save(state_key, sample_state, sample_metadata)

        # Manually modify the saved file to have wrong schema version
        state_path = backend._get_state_path(state_key)
        with open(state_path) as f:
            data = json.load(f)

        data["schema_version"] = "999.0"  # Invalid version

        with open(state_path, "w") as f:
            json.dump(data, f)

        # Loading should return None due to version mismatch
        loaded_data = await backend.load_state(state_key)
        assert loaded_data is None

    @pytest.mark.asyncio
    async def test_concurrent_write_safety(self, backend, sample_state, sample_metadata):
        """Test that concurrent writes don't corrupt files."""
        state_key = "test_user:session1"

        # Simulate concurrent writes by patching the file operations
        original_save = backend.save
        call_count = 0

        async def concurrent_save(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return await original_save(*args, **kwargs)

        # Both saves should succeed due to file locking
        results = await asyncio.gather(
            concurrent_save(state_key, sample_state, sample_metadata),
            concurrent_save(state_key, sample_state, sample_metadata),
            return_exceptions=True,
        )

        # At least one should succeed
        assert any(r is True for r in results)

        # File should be readable
        loaded_data = await backend.load_state(state_key)
        assert loaded_data is not None

    @pytest.mark.asyncio
    async def test_corrupted_file_handling(self, backend):
        """Test handling of corrupted state files."""
        state_key = "test_user:session1"

        # Create a corrupted file
        state_path = backend._get_state_path(state_key)
        state_path.parent.mkdir(parents=True, exist_ok=True)

        with open(state_path, "w") as f:
            f.write("invalid json content")

        # Loading should return None for corrupted files
        loaded_data = await backend.load_state(state_key)
        assert loaded_data is None

    @pytest.mark.asyncio
    async def test_list_states(self, backend, sample_state, sample_metadata):
        """Test listing states for a user."""
        user_id = "test_user"

        # Save multiple states
        state_keys = [f"{user_id}:session1", f"{user_id}:session2"]
        for key in state_keys:
            await backend.save(key, sample_state, sample_metadata)

        # List states
        states = await backend.list_states(user_id)

        # Should find the states
        expected_states = [f"{user_id}:session1", f"{user_id}:session2"]
        assert len(states) == 2
        for expected_state in expected_states:
            assert expected_state in states
