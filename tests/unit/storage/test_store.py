"""Tests for storage protocol interface."""

from unittest.mock import AsyncMock, Mock

import pytest

from cogency.storage.store import Store


class MockStore:
    """Concrete implementation of Store protocol for testing."""

    async def save_profile(self, state_key: str, profile) -> bool:
        return True

    async def load_profile(self, state_key: str):
        return None

    async def delete_profile(self, state_key: str) -> bool:
        return True

    async def save_conversation(self, conversation) -> bool:
        return True

    async def load_conversation(self, conversation_id: str, user_id: str):
        return None

    async def delete_conversation(self, conversation_id: str) -> bool:
        return True

    async def save_workspace(self, workspace) -> bool:
        return True

    async def load_workspace(self, conversation_id: str, user_id: str):
        return None

    async def delete_workspace(self, conversation_id: str) -> bool:
        return True

    async def save_knowledge(self, artifact) -> bool:
        return True

    async def search_knowledge(
        self, query: str, user_id: str = "default", top_k: int = 5, threshold: float = 0.7
    ):
        return []

    async def load_knowledge(self, topic: str, user_id: str):
        return None

    async def delete_knowledge(self, topic: str, user_id: str) -> bool:
        return True


def test_store_protocol_detection():
    """Test Store protocol detection."""
    mock_store = MockStore()

    # Should be recognized as Store implementation
    assert isinstance(mock_store, Store)


def test_store_protocol_validation():
    """Test Store protocol validates required methods."""

    class IncompleteStore:
        async def save_profile(self, state_key: str, profile) -> bool:
            return True

        # Missing other required methods

    incomplete = IncompleteStore()

    # Should NOT be recognized as complete Store
    assert not isinstance(incomplete, Store)


def test_store_protocol_method_signatures():
    """Test Store protocol enforces correct method signatures."""
    mock_store = MockStore()

    # Check that all required methods exist and are callable
    assert hasattr(mock_store, "save_profile")
    assert callable(mock_store.save_profile)

    assert hasattr(mock_store, "load_profile")
    assert callable(mock_store.load_profile)

    assert hasattr(mock_store, "delete_profile")
    assert callable(mock_store.delete_profile)

    assert hasattr(mock_store, "save_conversation")
    assert callable(mock_store.save_conversation)

    assert hasattr(mock_store, "load_conversation")
    assert callable(mock_store.load_conversation)

    assert hasattr(mock_store, "delete_conversation")
    assert callable(mock_store.delete_conversation)

    assert hasattr(mock_store, "save_workspace")
    assert callable(mock_store.save_workspace)

    assert hasattr(mock_store, "load_workspace")
    assert callable(mock_store.load_workspace)

    assert hasattr(mock_store, "delete_workspace")
    assert callable(mock_store.delete_workspace)

    assert hasattr(mock_store, "save_knowledge")
    assert callable(mock_store.save_knowledge)

    assert hasattr(mock_store, "search_knowledge")
    assert callable(mock_store.search_knowledge)

    assert hasattr(mock_store, "load_knowledge")
    assert callable(mock_store.load_knowledge)

    assert hasattr(mock_store, "delete_knowledge")
    assert callable(mock_store.delete_knowledge)


@pytest.mark.asyncio
async def test_store_profile_operations():
    """Test Store profile operation interface."""
    mock_store = MockStore()
    mock_profile = Mock()

    # Test profile operations
    result = await mock_store.save_profile("test_key", mock_profile)
    assert result is True

    result = await mock_store.load_profile("test_key")
    assert result is None  # MockStore returns None

    result = await mock_store.delete_profile("test_key")
    assert result is True


@pytest.mark.asyncio
async def test_store_conversation_operations():
    """Test Store conversation operation interface."""
    mock_store = MockStore()
    mock_conversation = Mock()

    # Test conversation operations
    result = await mock_store.save_conversation(mock_conversation)
    assert result is True

    result = await mock_store.load_conversation("conv_id", "user_id")
    assert result is None

    result = await mock_store.delete_conversation("conv_id")
    assert result is True


@pytest.mark.asyncio
async def test_store_workspace_operations():
    """Test Store workspace operation interface."""
    mock_store = MockStore()
    mock_workspace = Mock()

    # Test workspace operations
    result = await mock_store.save_workspace(mock_workspace)
    assert result is True

    result = await mock_store.load_workspace("conv_id", "user_id")
    assert result is None

    result = await mock_store.delete_workspace("conv_id")
    assert result is True


@pytest.mark.asyncio
async def test_store_knowledge_operations():
    """Test Store knowledge operation interface."""
    mock_store = MockStore()
    mock_artifact = Mock()

    # Test knowledge operations
    result = await mock_store.save_knowledge(mock_artifact)
    assert result is True

    result = await mock_store.search_knowledge("test query")
    assert result == []

    result = await mock_store.search_knowledge(
        "test query", user_id="user123", top_k=10, threshold=0.8
    )
    assert result == []

    result = await mock_store.load_knowledge("topic", "user_id")
    assert result is None

    result = await mock_store.delete_knowledge("topic", "user_id")
    assert result is True


def test_store_protocol_with_mock():
    """Test Store protocol works with unittest.Mock."""
    # Create mock that implements all Store methods
    mock_store = Mock(spec=Store)

    # Should be recognized as Store
    assert isinstance(mock_store, Store)


def test_store_protocol_runtime_checkable():
    """Test Store is runtime checkable."""
    # Should be able to use isinstance at runtime
    mock_store = MockStore()

    # This should work without type errors
    if isinstance(mock_store, Store):
        assert True
    else:
        pytest.fail("Store protocol should be runtime checkable")


class ExtendedStore(MockStore):
    """Extended store with additional methods."""

    async def custom_operation(self) -> str:
        return "custom"


def test_store_protocol_extensibility():
    """Test Store protocol allows extension."""
    extended_store = ExtendedStore()

    # Should still be recognized as Store
    assert isinstance(extended_store, Store)

    # Should also have custom methods
    assert hasattr(extended_store, "custom_operation")


@pytest.mark.asyncio
async def test_store_protocol_async_nature():
    """Test all Store methods are properly async."""
    mock_store = MockStore()

    # All methods should return coroutines
    import inspect

    for method_name in [
        "save_profile",
        "load_profile",
        "delete_profile",
        "save_conversation",
        "load_conversation",
        "delete_conversation",
        "save_workspace",
        "load_workspace",
        "delete_workspace",
        "save_knowledge",
        "search_knowledge",
        "load_knowledge",
        "delete_knowledge",
    ]:
        method = getattr(mock_store, method_name)
        assert inspect.iscoroutinefunction(method), f"{method_name} should be async"


def test_store_protocol_type_annotations():
    """Test Store protocol preserves type information."""
    # This is mainly a compile-time test, but we can check basic structure
    mock_store = MockStore()

    # Methods should exist and be callable
    methods = [
        "save_profile",
        "load_profile",
        "delete_profile",
        "save_conversation",
        "load_conversation",
        "delete_conversation",
        "save_workspace",
        "load_workspace",
        "delete_workspace",
        "save_knowledge",
        "search_knowledge",
        "load_knowledge",
        "delete_knowledge",
    ]

    for method_name in methods:
        assert hasattr(mock_store, method_name)
        method = getattr(mock_store, method_name)
        assert callable(method)


class AsyncMockStore:
    """Store implementation using AsyncMock for testing async behavior."""

    def __init__(self):
        # Profile operations
        self.save_profile = AsyncMock(return_value=True)
        self.load_profile = AsyncMock(return_value=None)
        self.delete_profile = AsyncMock(return_value=True)

        # Conversation operations
        self.save_conversation = AsyncMock(return_value=True)
        self.load_conversation = AsyncMock(return_value=None)
        self.delete_conversation = AsyncMock(return_value=True)

        # Workspace operations
        self.save_workspace = AsyncMock(return_value=True)
        self.load_workspace = AsyncMock(return_value=None)
        self.delete_workspace = AsyncMock(return_value=True)

        # Knowledge operations
        self.save_knowledge = AsyncMock(return_value=True)
        self.search_knowledge = AsyncMock(return_value=[])
        self.load_knowledge = AsyncMock(return_value=None)
        self.delete_knowledge = AsyncMock(return_value=True)


@pytest.mark.asyncio
async def test_store_with_async_mocks():
    """Test Store protocol with AsyncMock implementations."""
    mock_store = AsyncMockStore()

    # Should be recognized as Store
    assert isinstance(mock_store, Store)

    # Test async operations work
    result = await mock_store.save_profile("key", Mock())
    assert result is True

    mock_store.save_profile.assert_called_once()

    # Test search_knowledge with parameters
    await mock_store.search_knowledge("query", user_id="user", top_k=10, threshold=0.5)
    mock_store.search_knowledge.assert_called_with("query", user_id="user", top_k=10, threshold=0.5)
