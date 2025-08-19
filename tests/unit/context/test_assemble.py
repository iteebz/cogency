"""Tests for context namespace API.

Tests define the expected context.assemble() interface for unified
context assembly with user-scoped data integration.
"""

import pytest

from cogency.context import context, working


class TestContextNamespace:
    """Test context namespace API for unified context assembly."""

    def test_assemble_basic_context(self):
        """Assemble creates basic context without user data."""
        query = "What is 2 + 2?"
        user_id = "test_user"
        tool_results = []

        result = context.assemble(query, user_id, tool_results)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_assemble_with_working_memory(self):
        """Assemble includes working memory in context assembly."""
        user_id = "working_test_user"
        query = "Continue with the file operations"

        # Set up working memory
        tool_results = [
            {"tool": "file_write", "result": "Created test.txt"},
            {"tool": "file_read", "result": "Content: hello world"},
        ]
        working.update(user_id, tool_results)

        # Assemble should include working memory
        result = context.assemble(query, user_id, working.get(user_id))

        assert isinstance(result, str)
        assert len(result) > len(query)

    def test_assemble_user_isolation(self):
        """Assemble maintains user isolation in context assembly."""
        user_a = "user_a"
        user_b = "user_b"
        query = "Help me"

        # Set up different contexts for each user
        working.update(user_a, [{"tool": "model_train", "result": "Training complete"}])
        working.update(user_b, [{"tool": "server_start", "result": "Server running"}])

        context_a = context.assemble(query, user_a, working.get(user_a))
        context_b = context.assemble(query, user_b, working.get(user_b))

        # Contexts should be different and isolated
        assert context_a != context_b
        assert isinstance(context_a, str)
        assert isinstance(context_b, str)

    def test_assemble_api_consistency(self):
        """Verify context namespace provides consistent API."""
        user_id = "api_test"
        query = "test"

        # Should work without error
        result = context.assemble(query, user_id, [])

        # Verify the API is available
        assert hasattr(context, "assemble")
        assert callable(context.assemble)
        assert isinstance(result, str)

    def test_assemble_empty_user_data(self):
        """Assemble handles users with no stored data gracefully."""
        user_id = "empty_user"
        query = "Simple question"
        tool_results = []

        # No memory or working data for this user
        result = context.assemble(query, user_id, tool_results)

        assert isinstance(result, str)
        assert len(result) >= len(query)


class TestContextIntegration:
    """Test context integration with other namespace modules."""

    def test_assemble_integrates_with_working(self):
        """Assemble properly integrates with working namespace."""
        user_id = "integration_test"
        query = "Continue task"

        # Use working namespace to set data
        tools = [{"tool": "test_tool", "result": "test_result"}]
        working.update(user_id, tools)

        # Assemble should access working data
        result = context.assemble(query, user_id, working.get(user_id))

        assert isinstance(result, str)

        # Clean up
        working.clear(user_id)
        assert working.get(user_id) == []


class TestContextEdgeCases:
    """Test edge cases and error conditions."""

    def test_assemble_none_user_id(self):
        """Assemble handles None user_id gracefully."""
        with pytest.raises((ValueError, TypeError)):
            context.assemble("test", None, [])

    def test_assemble_empty_query(self):
        """Assemble handles empty query string."""
        result = context.assemble("", "test_user", [])
        assert isinstance(result, str)
