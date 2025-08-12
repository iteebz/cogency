"""Unit tests for state-driven event orchestration."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from cogency.events.orchestration import (
    state_event,
    extract_conversation_data,
    extract_profile_data,
    extract_workspace_data,
    extract_knowledge_data,
    extract_delete_data,
)


class TestStateEventDecorator:
    """Test state_event decorator functionality."""
    
    @pytest.fixture
    def mock_emit(self, monkeypatch):
        """Mock emit function for testing."""
        mock = MagicMock()
        monkeypatch.setattr("cogency.events.orchestration.emit", mock)
        return mock
    
    @pytest.mark.asyncio
    async def test_state_event_success(self, mock_emit):
        """Test state_event decorator emits success event when mutation succeeds."""
        
        @state_event("test_event")
        async def successful_mutation():
            return True
        
        result = await successful_mutation()
        
        assert result is True
        mock_emit.assert_called_once_with("test_event", success=True)
    
    @pytest.mark.asyncio
    async def test_state_event_failure(self, mock_emit):
        """Test state_event decorator emits failure event when mutation fails."""
        
        @state_event("test_event")
        async def failed_mutation():
            return False
        
        result = await failed_mutation()
        
        assert result is False
        mock_emit.assert_called_once_with("test_event", success=False)
    
    @pytest.mark.asyncio
    async def test_state_event_with_data_extractor(self, mock_emit):
        """Test state_event decorator with data extraction."""
        
        def extract_test_data(args, kwargs, result):
            return {"test_key": "test_value"}
        
        @state_event("test_event", extract_test_data)
        async def mutation_with_data():
            return True
        
        await mutation_with_data()
        
        mock_emit.assert_called_once_with("test_event", success=True, test_key="test_value")
    
    @pytest.mark.asyncio
    async def test_state_event_preserves_function_metadata(self, mock_emit):
        """Test decorator preserves original function metadata."""
        
        @state_event("test_event")
        async def documented_function():
            """This function has documentation."""
            return True
        
        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This function has documentation."


class TestDataExtractors:
    """Test data extraction functions."""
    
    def test_extract_conversation_data_with_args(self):
        """Test conversation data extraction from positional args."""
        mock_conversation = MagicMock()
        mock_conversation.conversation_id = "conv_123"
        mock_conversation.user_id = "user_456"
        mock_conversation.messages = [1, 2, 3]
        
        args = (None, mock_conversation)  # self, conversation
        kwargs = {}
        result = True
        
        data = extract_conversation_data(args, kwargs, result)
        
        assert data == {
            "conversation_id": "conv_123",
            "user_id": "user_456",
            "message_count": 3
        }
    
    def test_extract_conversation_data_with_kwargs(self):
        """Test conversation data extraction from keyword args."""
        mock_conversation = MagicMock()
        mock_conversation.conversation_id = "conv_789"
        mock_conversation.user_id = "user_012"
        mock_conversation.messages = []
        
        args = ()
        kwargs = {"conversation": mock_conversation}
        result = True
        
        data = extract_conversation_data(args, kwargs, result)
        
        assert data == {
            "conversation_id": "conv_789",
            "user_id": "user_012", 
            "message_count": 0
        }
    
    def test_extract_conversation_data_missing(self):
        """Test conversation data extraction with missing conversation."""
        args = ()
        kwargs = {}
        result = True
        
        data = extract_conversation_data(args, kwargs, result)
        
        assert data == {}
    
    def test_extract_profile_data_with_args(self):
        """Test profile data extraction from positional args."""
        mock_profile = MagicMock()
        mock_profile.user_id = "profile_user"
        
        args = (None, "state_key_123", mock_profile)  # self, state_key, profile
        kwargs = {}
        result = True
        
        data = extract_profile_data(args, kwargs, result)
        
        assert data == {
            "state_key": "state_key_123",
            "user_id": "profile_user"
        }
    
    def test_extract_profile_data_no_user_id(self):
        """Test profile data extraction when profile has no user_id."""
        mock_profile = MagicMock()
        del mock_profile.user_id  # Remove user_id attribute
        
        args = (None, "state_key_456")
        kwargs = {"profile": mock_profile}
        result = True
        
        data = extract_profile_data(args, kwargs, result)
        
        assert data == {"state_key": "state_key_456"}
    
    def test_extract_workspace_data_with_args(self):
        """Test workspace data extraction from positional args."""
        mock_workspace = MagicMock()
        mock_workspace.conversation_id = "workspace_conv"
        
        args = (None, "task_123", "user_456", mock_workspace)  # self, task_id, user_id, workspace
        kwargs = {}
        result = True
        
        data = extract_workspace_data(args, kwargs, result)
        
        assert data == {
            "task_id": "task_123",
            "user_id": "user_456",
            "conversation_id": "workspace_conv"
        }
    
    def test_extract_workspace_data_with_kwargs(self):
        """Test workspace data extraction from keyword args."""
        mock_workspace = MagicMock()
        mock_workspace.conversation_id = "kwargs_conv"
        
        args = ()
        kwargs = {
            "task_id": "kwargs_task",
            "user_id": "kwargs_user",
            "workspace": mock_workspace
        }
        result = True
        
        data = extract_workspace_data(args, kwargs, result)
        
        assert data == {
            "task_id": "kwargs_task", 
            "user_id": "kwargs_user",
            "conversation_id": "kwargs_conv"
        }
    
    def test_extract_knowledge_data_with_args(self):
        """Test knowledge data extraction from positional args."""
        mock_artifact = MagicMock()
        mock_artifact.topic = "test_topic"
        mock_artifact.user_id = "knowledge_user"
        mock_artifact.content_type = "text/plain"
        
        args = (None, mock_artifact)  # self, artifact
        kwargs = {}
        result = True
        
        data = extract_knowledge_data(args, kwargs, result)
        
        assert data == {
            "topic": "test_topic",
            "user_id": "knowledge_user",
            "content_type": "text/plain"
        }
    
    def test_extract_knowledge_data_missing(self):
        """Test knowledge data extraction with missing artifact."""
        args = ()
        kwargs = {}
        result = True
        
        data = extract_knowledge_data(args, kwargs, result)
        
        assert data == {}
    
    def test_extract_delete_data_with_args(self):
        """Test delete data extraction from positional args."""
        args = (None, "delete_id_123")  # self, id
        kwargs = {}
        result = True
        
        data = extract_delete_data(args, kwargs, result)
        
        assert data == {"target_id": "delete_id_123"}
    
    def test_extract_delete_data_insufficient_args(self):
        """Test delete data extraction with insufficient args."""
        args = (None,)  # Only self
        kwargs = {}
        result = True
        
        data = extract_delete_data(args, kwargs, result)
        
        assert data == {}


class TestIntegrationWithStorage:
    """Integration tests with storage layer methods."""
    
    @pytest.mark.asyncio
    async def test_decorated_save_conversation(self, monkeypatch):
        """Test save_conversation with orchestration decorator."""
        
        # Create a simple mock that succeeds
        async def mock_save_conversation_impl(self, conversation):
            return True
        
        # Apply decorator to mock
        from cogency.events.orchestration import state_event, extract_conversation_data
        decorated_method = state_event("conversation_saved", extract_conversation_data)(mock_save_conversation_impl)
        
        # Mock emit
        mock_emit_func = MagicMock()
        monkeypatch.setattr("cogency.events.orchestration.emit", mock_emit_func)
        
        # Create mock conversation with expected attributes
        mock_conversation = MagicMock()
        mock_conversation.conversation_id = "test_conv"
        mock_conversation.user_id = "test_user" 
        mock_conversation.messages = ["msg1", "msg2"]
        
        # Create mock storage instance
        storage = MagicMock()
        
        # Test the decorated method
        result = await decorated_method(storage, mock_conversation)
        
        # Verify state mutation succeeded
        assert result is True
        
        # Verify event was emitted with correct data
        mock_emit_func.assert_called_once_with(
            "conversation_saved",
            success=True,
            conversation_id="test_conv",
            user_id="test_user",
            message_count=2
        )
    
    @pytest.mark.asyncio
    async def test_decorated_save_conversation_failure(self, monkeypatch):
        """Test save_conversation failure with orchestration decorator."""
        from cogency.storage.sqlite.conversations import ConversationOperations
        
        # Mock to cause the method to return False (simulating database failure)
        async def mock_save_conversation_impl(self, conversation):
            # Simulate the original method's exception handling
            try:
                raise Exception("Database error") 
            except Exception:
                return False
        
        # Replace the entire method implementation
        monkeypatch.setattr(ConversationOperations, "save_conversation", mock_save_conversation_impl)
        
        # Now apply the decorator to our mock
        from cogency.events.orchestration import state_event, extract_conversation_data
        decorated_method = state_event("conversation_saved", extract_conversation_data)(mock_save_conversation_impl)
        monkeypatch.setattr(ConversationOperations, "save_conversation", decorated_method)
        
        # Mock emit
        mock_emit_func = MagicMock()
        monkeypatch.setattr("cogency.events.orchestration.emit", mock_emit_func)
        
        mock_conversation = MagicMock()
        
        storage = ConversationOperations()
        result = await storage.save_conversation(mock_conversation)
        
        # Verify failure handling
        assert result is False
        mock_emit_func.assert_called_once_with("conversation_saved", success=False)