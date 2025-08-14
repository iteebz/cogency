"""Unit tests for SQLite conversation operations - canonical storage implementation."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from cogency.context.conversation import Conversation
from cogency.storage.sqlite.conversations import (
    _ensure_schema,
)


@pytest.fixture
async def temp_conversation_store():
    """Temporary SQLite conversation store for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_conversations.db"

        # Initialize schema
        await _ensure_schema(str(db_path))
        yield str(db_path)


@pytest.fixture
def sample_conversation():
    """Sample conversation for testing."""
    return Conversation(
        conversation_id="test-conv-123",
        user_id="test-user",
        messages=[
            {"role": "user", "content": "What is Python?"},
            {"role": "assistant", "content": "Python is a programming language."},
        ],
    )


@pytest.fixture
def sample_conversations():
    """Multiple sample conversations for testing."""
    return [
        Conversation(
            conversation_id="conv-001",
            user_id="user-001",
            messages=[
                {"role": "user", "content": "Hello, how are you today?"},
                {"role": "assistant", "content": "I'm doing well, thank you for asking!"},
            ],
        ),
        Conversation(
            conversation_id="conv-002",
            user_id="user-001",
            messages=[
                {"role": "user", "content": "Tell me about machine learning"},
                {"role": "assistant", "content": "Machine learning is a subset of AI..."},
            ],
        ),
        Conversation(
            conversation_id="conv-003",
            user_id="user-002",
            messages=[
                {"role": "user", "content": "What's the weather?"},
                {"role": "assistant", "content": "I don't have access to weather data."},
            ],
        ),
        Conversation(
            conversation_id="conv-004",
            user_id="user-001",
            messages=[],  # Empty conversation
        ),
    ]


class TestConversationOperations:
    """Test conversation CRUD operations."""

    @pytest.mark.asyncio
    async def test_save_and_load_conversation(self, temp_conversation_store, sample_conversation):
        """Test basic save/load cycle."""
        store = temp_conversation_store

        # Save conversation
        result = await store.save_conversation(sample_conversation)
        assert result is True

        # Load conversation
        loaded = await store.load_conversation("test-conv-123", "test-user")
        assert loaded is not None
        assert loaded.conversation_id == "test-conv-123"
        assert loaded.user_id == "test-user"
        assert len(loaded.messages) == 2
        assert loaded.messages[0]["content"] == "What is Python?"

    @pytest.mark.asyncio
    async def test_load_nonexistent_conversation(self, temp_conversation_store):
        """Test loading conversation that doesn't exist."""
        store = temp_conversation_store

        result = await store.load_conversation("nonexistent", "test-user")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_conversation(self, temp_conversation_store, sample_conversation):
        """Test conversation deletion."""
        store = temp_conversation_store

        # Save then delete
        await store.save_conversation(sample_conversation)
        result = await store.delete_conversation("test-conv-123")
        assert result is True

        # Verify deleted
        loaded = await store.load_conversation("test-conv-123", "test-user")
        assert loaded is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_conversation(self, temp_conversation_store):
        """Test deleting conversation that doesn't exist."""
        store = temp_conversation_store

        result = await store.delete_conversation("nonexistent")
        assert result is False


class TestListConversations:
    """Test list_conversations functionality - the new method we added."""

    @pytest.mark.asyncio
    async def test_list_conversations_empty(self, temp_conversation_store):
        """Test listing conversations when none exist."""
        store = temp_conversation_store

        conversations = await store.list_conversations("test-user")
        assert conversations == []

    @pytest.mark.asyncio
    async def test_list_conversations_basic(self, temp_conversation_store, sample_conversations):
        """Test listing conversations returns expected format."""
        store = temp_conversation_store

        # Save multiple conversations
        for conv in sample_conversations:
            await store.save_conversation(conv)

        # List conversations for user-001
        conversations = await store.list_conversations("user-001")

        # Should return 3 conversations (conv-001, conv-002, conv-004)
        assert len(conversations) == 3

        # Check format of returned data
        for conv in conversations:
            assert "conversation_id" in conv
            assert "title" in conv
            assert "updated_at" in conv
            assert "message_count" in conv

            # Validate types
            assert isinstance(conv["conversation_id"], str)
            assert isinstance(conv["title"], str)
            assert isinstance(conv["updated_at"], str)
            assert isinstance(conv["message_count"], int)

    @pytest.mark.asyncio
    async def test_list_conversations_user_isolation(
        self, temp_conversation_store, sample_conversations
    ):
        """Test conversations are properly isolated by user."""
        store = temp_conversation_store

        # Save conversations for different users
        for conv in sample_conversations:
            await store.save_conversation(conv)

        # List conversations for user-001
        user1_conversations = await store.list_conversations("user-001")
        assert len(user1_conversations) == 3  # conv-001, conv-002, conv-004

        # List conversations for user-002
        user2_conversations = await store.list_conversations("user-002")
        assert len(user2_conversations) == 1  # conv-003

        # Verify conversation IDs
        user1_ids = {conv["conversation_id"] for conv in user1_conversations}
        user2_ids = {conv["conversation_id"] for conv in user2_conversations}

        assert user1_ids == {"conv-001", "conv-002", "conv-004"}
        assert user2_ids == {"conv-003"}

    @pytest.mark.asyncio
    async def test_list_conversations_ordering(self, temp_conversation_store):
        """Test conversations are ordered consistently (validates SQL ORDER BY works)."""
        store = temp_conversation_store

        conversations = [
            Conversation(
                conversation_id="conv-alpha",
                user_id="test-user",
                messages=[{"role": "user", "content": "Alpha message"}],
            ),
            Conversation(
                conversation_id="conv-beta",
                user_id="test-user",
                messages=[{"role": "user", "content": "Beta message"}],
            ),
            Conversation(
                conversation_id="conv-gamma",
                user_id="test-user",
                messages=[{"role": "user", "content": "Gamma message"}],
            ),
        ]

        # Save conversations
        for conv in conversations:
            await store.save_conversation(conv)

        # List conversations multiple times to ensure consistent ordering
        result1 = await store.list_conversations("test-user")
        result2 = await store.list_conversations("test-user")

        # Should return all 3 conversations
        assert len(result1) == 3
        assert len(result2) == 3

        # Ordering should be consistent between calls
        ids1 = [conv["conversation_id"] for conv in result1]
        ids2 = [conv["conversation_id"] for conv in result2]
        assert ids1 == ids2

        # All conversation IDs should be present
        all_ids = set(ids1)
        assert all_ids == {"conv-alpha", "conv-beta", "conv-gamma"}

    @pytest.mark.asyncio
    async def test_list_conversations_limit(self, temp_conversation_store):
        """Test limit parameter works correctly."""
        store = temp_conversation_store

        # Create 5 conversations
        conversations = []
        for i in range(5):
            conv = Conversation(
                conversation_id=f"conv-{i:03d}",
                user_id="test-user",
                messages=[{"role": "user", "content": f"Message {i}"}],
            )
            conversations.append(conv)
            await store.save_conversation(conv)

        # Test different limits
        result_2 = await store.list_conversations("test-user", limit=2)
        assert len(result_2) == 2

        result_10 = await store.list_conversations("test-user", limit=10)
        assert len(result_10) == 5  # Can't return more than exist

        result_0 = await store.list_conversations("test-user", limit=0)
        assert len(result_0) == 0

    @pytest.mark.asyncio
    async def test_list_conversations_message_count(self, temp_conversation_store):
        """Test message_count field is accurate."""
        store = temp_conversation_store

        conversations = [
            Conversation(conversation_id="empty-conv", user_id="test-user", messages=[]),
            Conversation(
                conversation_id="single-conv",
                user_id="test-user",
                messages=[{"role": "user", "content": "Hello"}],
            ),
            Conversation(
                conversation_id="multi-conv",
                user_id="test-user",
                messages=[
                    {"role": "user", "content": "Question"},
                    {"role": "assistant", "content": "Answer"},
                    {"role": "user", "content": "Follow-up"},
                ],
            ),
        ]

        for conv in conversations:
            await store.save_conversation(conv)

        result = await store.list_conversations("test-user")

        # Find conversations by ID and check message counts
        conv_counts = {conv["conversation_id"]: conv["message_count"] for conv in result}

        assert conv_counts["empty-conv"] == 0
        assert conv_counts["single-conv"] == 1
        assert conv_counts["multi-conv"] == 3


class TestTitleExtraction:
    """Test conversation title extraction logic."""

    @pytest.mark.asyncio
    async def test_title_from_first_user_message(self, temp_conversation_store):
        """Test title is extracted from first user message."""
        store = temp_conversation_store

        conv = Conversation(
            conversation_id="title-test",
            user_id="test-user",
            messages=[
                {"role": "user", "content": "How do I learn Python programming?"},
                {"role": "assistant", "content": "Great question! Here's how..."},
            ],
        )

        await store.save_conversation(conv)
        result = await store.list_conversations("test-user")

        assert len(result) == 1
        assert result[0]["title"] == "How do I learn Python programming?"

    @pytest.mark.asyncio
    async def test_title_truncation(self, temp_conversation_store):
        """Test long titles are truncated properly."""
        store = temp_conversation_store

        long_message = "This is a very long user message that should be truncated because it exceeds the maximum length limit for conversation titles"

        conv = Conversation(
            conversation_id="long-title-test",
            user_id="test-user",
            messages=[{"role": "user", "content": long_message}],
        )

        await store.save_conversation(conv)
        result = await store.list_conversations("test-user")

        assert len(result) == 1
        title = result[0]["title"]
        assert len(title) <= 60  # Should be truncated
        assert title.endswith("...")  # Should have ellipsis
        assert title.startswith("This is a very long user message")

    @pytest.mark.asyncio
    async def test_title_empty_conversation(self, temp_conversation_store):
        """Test title for conversation with no messages."""
        store = temp_conversation_store

        conv = Conversation(conversation_id="empty-test", user_id="test-user", messages=[])

        await store.save_conversation(conv)
        result = await store.list_conversations("test-user")

        assert len(result) == 1
        assert result[0]["title"] == "Empty conversation"

    @pytest.mark.asyncio
    async def test_title_no_user_messages(self, temp_conversation_store):
        """Test title when no user messages exist (only assistant)."""
        store = temp_conversation_store

        conv = Conversation(
            conversation_id="no-user-test",
            user_id="test-user",
            messages=[
                {"role": "assistant", "content": "I'm an assistant message"},
                {"role": "system", "content": "System message"},
            ],
        )

        await store.save_conversation(conv)
        result = await store.list_conversations("test-user")

        assert len(result) == 1
        assert result[0]["title"] == "No user messages"

    @pytest.mark.asyncio
    async def test_title_skips_assistant_messages(self, temp_conversation_store):
        """Test title extraction skips assistant messages to find first user message."""
        store = temp_conversation_store

        conv = Conversation(
            conversation_id="skip-test",
            user_id="test-user",
            messages=[
                {"role": "assistant", "content": "Assistant opening"},
                {"role": "system", "content": "System message"},
                {"role": "user", "content": "First user message here"},
                {"role": "assistant", "content": "Response"},
            ],
        )

        await store.save_conversation(conv)
        result = await store.list_conversations("test-user")

        assert len(result) == 1
        assert result[0]["title"] == "First user message here"


class TestErrorHandling:
    """Test error handling in conversation operations."""

    @pytest.mark.asyncio
    async def test_list_conversations_database_error(self, temp_conversation_store):
        """Test list_conversations handles database errors gracefully."""
        store = temp_conversation_store

        # Close the database connection to simulate error
        await store.close() if hasattr(store, "close") else None

        # Should return empty list instead of crashing
        conversations = await store.list_conversations("test-user")
        assert conversations == []

    @pytest.mark.asyncio
    async def test_list_conversations_corrupted_data(self, temp_conversation_store):
        """Test list_conversations handles corrupted JSON gracefully."""
        store = temp_conversation_store

        # Manually insert corrupted data
        import aiosqlite

        async with aiosqlite.connect(store.db_path) as db:
            await db.execute(
                """
                INSERT INTO conversations (conversation_id, user_id, conversation_data, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """,
                ("corrupt-conv", "test-user", "invalid-json-data"),
            )
            await db.commit()

        # Should handle corrupted data gracefully
        conversations = await store.list_conversations("test-user")
        # Should return empty list or skip corrupted entries
        assert isinstance(conversations, list)

    @pytest.mark.asyncio
    async def test_title_extraction_handles_none_content(self, temp_conversation_store):
        """Test title extraction handles messages with None content."""
        store = temp_conversation_store

        conv = Conversation(
            conversation_id="none-content-test",
            user_id="test-user",
            messages=[
                {"role": "user", "content": None},  # None content
                {"role": "user", "content": "Real message"},
            ],
        )

        await store.save_conversation(conv)
        result = await store.list_conversations("test-user")

        assert len(result) == 1
        # Should skip None content and find real message
        assert result[0]["title"] == "Real message"


class TestIntegrationWithEvents:
    """Test integration with event system."""

    @pytest.mark.asyncio
    async def test_save_conversation_emits_event(
        self, temp_conversation_store, sample_conversation
    ):
        """Test that save_conversation emits proper event."""
        store = temp_conversation_store

        with patch("cogency.events.orchestration.emit") as mock_emit:
            result = await store.save_conversation(sample_conversation)

            assert result is True
            mock_emit.assert_called_once_with(
                "conversation_saved",
                success=True,
                conversation_id=sample_conversation.conversation_id,
                user_id=sample_conversation.user_id,
                message_count=2,
            )

    @pytest.mark.asyncio
    async def test_delete_conversation_emits_event(
        self, temp_conversation_store, sample_conversation
    ):
        """Test that delete_conversation emits proper event."""
        store = temp_conversation_store

        # Save first
        await store.save_conversation(sample_conversation)

        with patch("cogency.events.orchestration.emit") as mock_emit:
            result = await store.delete_conversation("test-conv-123")

            assert result is True
            mock_emit.assert_called_once_with(
                "conversation_deleted", success=True, target_id="test-conv-123"
            )
