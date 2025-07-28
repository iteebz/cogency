"""Unit tests for state persistence manager."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from cogency.state import State
from cogency.persistence.manager import StateManager
from cogency.persistence.backends import StateBackend


class MockBackend(StateBackend):
    """Mock backend for testing."""
    
    def __init__(self):
        self.states = {}
        self.process_id = "mock_process"
    
    async def save_state(self, state_key: str, state: State, metadata: dict) -> bool:
        self.states[state_key] = {"state": state, "metadata": metadata, "schema_version": "1.0"}
        return True
    
    async def load_state(self, state_key: str) -> dict:
        data = self.states.get(state_key)
        if data:
            # Convert State object back to dict format expected by manager
            return {
                "state": data["state"].__dict__ if hasattr(data["state"], '__dict__') else data["state"],
                "metadata": data["metadata"],
                "schema_version": data["schema_version"]
            }
        return None
    
    async def delete_state(self, state_key: str) -> bool:
        if state_key in self.states:
            del self.states[state_key]
            return True
        return False
    
    async def list_states(self, user_id: str) -> list:
        return [k for k in self.states.keys() if k.startswith(user_id)]


class TestStateManager:
    """Test state persistence manager."""
    
    @pytest.fixture
    def mock_backend(self):
        return MockBackend()
    
    @pytest.fixture
    def manager(self, mock_backend):
        return StateManager(backend=mock_backend)
    
    @pytest.fixture
    def sample_state(self):
        state = State(query="test query", user_id="test_user")
        state.add_message("user", "Hello")
        state.add_message("assistant", "Hi there")
        return state
    
    @pytest.mark.asyncio
    async def test_save_state_with_metadata(self, manager, sample_state):
        """Test saving state with proper metadata."""
        success = await manager.save_state(
            sample_state,
            llm_provider="openai",
            llm_model="gpt-4",
            tools_count=3,
            memory_backend="filesystem",
            timestamp="2024-01-01T00:00:00"
        )
        
        assert success is True
        
        # Verify state was saved with correct metadata
        state_key = manager._generate_state_key("test_user")
        stored_data = await manager.backend.load_state(state_key)
        
        assert stored_data is not None
        assert stored_data["metadata"]["llm_provider"] == "openai"
        assert stored_data["metadata"]["llm_model"] == "gpt-4"
        assert stored_data["metadata"]["tools_count"] == 3
        assert stored_data["metadata"]["memory_backend"] == "filesystem"
    
    @pytest.mark.asyncio
    async def test_load_state_with_validation(self, manager, sample_state):
        """Test loading state with LLM validation."""
        # Save state
        await manager.save_state(
            sample_state,
            llm_provider="openai",
            llm_model="gpt-4"
        )
        
        # Load with matching provider/model - should succeed
        loaded_state = await manager.load_state(
            "test_user",
            validate_llm=True,
            expected_llm_provider="openai",
            expected_llm_model="gpt-4"
        )
        
        assert loaded_state is not None
        assert loaded_state.user_id == "test_user"
        assert loaded_state.query == "test query"
        assert len(loaded_state.messages) == 2
    
    @pytest.mark.asyncio
    async def test_load_state_provider_mismatch(self, manager, sample_state):
        """Test loading state with provider mismatch."""
        # Save with openai
        await manager.save_state(
            sample_state,
            llm_provider="openai",
            llm_model="gpt-4"
        )
        
        # Try to load expecting claude - should fail
        loaded_state = await manager.load_state(
            "test_user",
            validate_llm=True,
            expected_llm_provider="anthropic"
        )
        
        assert loaded_state is None
    
    @pytest.mark.asyncio
    async def test_load_state_model_mismatch(self, manager, sample_state):
        """Test loading state with model mismatch."""
        # Save with gpt-4
        await manager.save_state(
            sample_state,
            llm_provider="openai", 
            llm_model="gpt-4"
        )
        
        # Try to load expecting gpt-3.5 - should fail
        loaded_state = await manager.load_state(
            "test_user",
            validate_llm=True,
            expected_llm_provider="openai",
            expected_llm_model="gpt-3.5-turbo"
        )
        
        assert loaded_state is None
    
    @pytest.mark.asyncio
    async def test_load_state_no_validation(self, manager, sample_state):
        """Test loading state without validation."""
        # Save state
        await manager.save_state(
            sample_state,
            llm_provider="openai",
            llm_model="gpt-4"
        )
        
        # Load without validation - should succeed regardless
        loaded_state = await manager.load_state("test_user", validate_llm=False)
        
        assert loaded_state is not None
        assert loaded_state.user_id == "test_user"
    
    @pytest.mark.asyncio
    async def test_disabled_manager(self, mock_backend):
        """Test manager with persistence disabled."""
        manager = StateManager(backend=mock_backend, enabled=False)
        sample_state = State(query="test", user_id="test_user")
        
        # Save should succeed silently
        success = await manager.save_state(sample_state)
        assert success is True
        
        # But nothing should be actually saved
        assert len(mock_backend.states) == 0
        
        # Load should return None
        loaded_state = await manager.load_state("test_user")
        assert loaded_state is None
    
    @pytest.mark.asyncio
    async def test_graceful_degradation_on_save_error(self, sample_state):
        """Test graceful degradation when save fails."""
        # Create backend that always fails
        failing_backend = AsyncMock()
        failing_backend.save_state.side_effect = Exception("Save failed")
        
        manager = StateManager(backend=failing_backend)
        
        # Should not raise exception, just return False
        success = await manager.save_state(sample_state)
        assert success is False
    
    @pytest.mark.asyncio
    async def test_graceful_degradation_on_load_error(self):
        """Test graceful degradation when load fails."""
        # Create backend that always fails
        failing_backend = AsyncMock()
        failing_backend.load_state.side_effect = Exception("Load failed")
        
        manager = StateManager(backend=failing_backend)
        
        # Should not raise exception, just return None
        loaded_state = await manager.load_state("test_user")
        assert loaded_state is None
    
    @pytest.mark.asyncio
    async def test_custom_metadata(self, manager, sample_state):
        """Test custom metadata handling."""
        success = await manager.save_state(
            sample_state,
            custom_session_id="abc123",
            custom_experiment="test_run"
        )
        
        assert success is True
        
        # Check custom metadata was stored
        state_key = manager._generate_state_key("test_user")
        stored_data = await manager.backend.load_state(state_key)
        
        assert stored_data["metadata"]["custom_session_id"] == "abc123"
        assert stored_data["metadata"]["custom_experiment"] == "test_run"
    
    @pytest.mark.asyncio
    async def test_state_reconstruction(self, manager, sample_state):
        """Test complete state reconstruction."""
        # Add more complex state data
        sample_state.iteration = 5
        sample_state.stop_reason = "max_iterations"
        sample_state.response = "Final response"
        sample_state.add_action(
            mode="fast",
            thinking="Test thinking",
            planning="Test planning", 
            reflection="Test reflection",
            approach="direct",
            tool_calls=[{"name": "test_tool", "args": {}}]
        )
        
        # Save and load
        await manager.save_state(sample_state)
        loaded_state = await manager.load_state("test_user", validate_llm=False)
        
        # Verify all fields reconstructed correctly
        assert loaded_state.iteration == 5
        assert loaded_state.stop_reason == "max_iterations"
        assert loaded_state.response == "Final response"
        assert len(loaded_state.actions) == 1
        assert loaded_state.actions[0]["thinking"] == "Test thinking"
        assert loaded_state.callback is None  # Should not persist callbacks