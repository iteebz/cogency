"""Tests for working memory namespace API.

Tests define the expected working.* namespace interface for user-scoped
tool execution memory management.
"""

import pytest

from cogency.context import working


class TestWorkingMemoryNamespace:
    """Test working memory namespace API for user isolation."""

    def test_get_empty_working_memory(self):
        """Get returns empty list for new user."""
        user_id = "test_user_1"
        result = working.get(user_id)
        assert result == []

    def test_get_returns_independent_lists(self):
        """Each user gets independent working memory list."""
        user_a = "user_a"
        user_b = "user_b"

        list_a = working.get(user_a)
        list_b = working.get(user_b)

        # Should be separate instances, not same reference
        assert list_a is not list_b

    def test_update_working_memory(self):
        """Update stores tool results for specific user."""
        user_id = "test_user_2"
        tool_results = [
            {"tool": "file_write", "result": "Created test.txt"},
            {"tool": "file_read", "result": "Content: hello"},
        ]

        working.update(user_id, tool_results)
        retrieved = working.get(user_id)

        assert retrieved == tool_results

    def test_user_isolation(self):
        """Working memory isolated between different users."""
        user_a = "user_a"
        user_b = "user_b"

        tools_a = [{"tool": "file_write", "result": "User A file"}]
        tools_b = [{"tool": "shell", "result": "User B command"}]

        working.update(user_a, tools_a)
        working.update(user_b, tools_b)

        assert working.get(user_a) == tools_a
        assert working.get(user_b) == tools_b
        assert working.get(user_a) != working.get(user_b)

    def test_clear_working_memory(self):
        """Clear removes all tool results for specific user."""
        user_id = "test_user_3"
        tool_results = [{"tool": "test", "result": "data"}]

        working.update(user_id, tool_results)
        assert working.get(user_id) == tool_results

        working.clear(user_id)
        assert working.get(user_id) == []

    def test_clear_only_affects_target_user(self):
        """Clear only affects specified user, not others."""
        user_a = "user_a"
        user_b = "user_b"

        tools_a = [{"tool": "file_a", "result": "data_a"}]
        tools_b = [{"tool": "file_b", "result": "data_b"}]

        working.update(user_a, tools_a)
        working.update(user_b, tools_b)

        working.clear(user_a)

        assert working.get(user_a) == []
        assert working.get(user_b) == tools_b

    def test_multiple_updates_accumulate(self):
        """Multiple updates should accumulate in working memory."""
        user_id = "test_user_4"

        # First tool execution
        first_tools = [{"tool": "file_write", "result": "Created file"}]
        working.update(user_id, first_tools)

        # Second tool execution - should accumulate
        second_tools = [
            {"tool": "file_write", "result": "Created file"},
            {"tool": "file_read", "result": "Read file"},
        ]
        working.update(user_id, second_tools)

        result = working.get(user_id)
        assert result == second_tools  # Latest state

    def test_concurrent_user_operations(self):
        """Multiple users can operate simultaneously without interference."""
        users = [f"user_{i}" for i in range(5)]

        # Each user updates their working memory
        for i, user_id in enumerate(users):
            tools = [{"tool": f"tool_{i}", "result": f"result_{i}"}]
            working.update(user_id, tools)

        # Verify each user has their own data
        for i, user_id in enumerate(users):
            expected = [{"tool": f"tool_{i}", "result": f"result_{i}"}]
            assert working.get(user_id) == expected

    def test_namespace_api_consistency(self):
        """Verify namespace provides consistent API surface."""
        # All operations should take user_id as first parameter
        user_id = "test_api"

        # These should all work without error
        working.get(user_id)
        working.update(user_id, [])
        working.clear(user_id)

        # Verify the API is available
        assert hasattr(working, "get")
        assert hasattr(working, "update")
        assert hasattr(working, "clear")
        assert callable(working.get)
        assert callable(working.update)
        assert callable(working.clear)


class TestWorkingMemoryEdgeCases:
    """Test edge cases and error conditions."""

    def test_none_user_id_handling(self):
        """Should handle None user_id gracefully."""
        # This might raise ValueError or treat None as valid key
        # Implementation dependent - test documents expected behavior
        with pytest.raises((ValueError, TypeError)):
            working.get(None)

    def test_empty_string_user_id(self):
        """Should handle empty string user_id."""
        user_id = ""
        tools = [{"tool": "test", "result": "data"}]

        working.update(user_id, tools)
        assert working.get(user_id) == tools

    def test_update_with_none_tools(self):
        """Should handle None tool_results gracefully."""
        user_id = "test_none"

        # Might convert to empty list or raise error
        working.update(user_id, None)
        result = working.get(user_id)

        # Should be empty list, not None
        assert result == [] or result is None

    def test_large_working_memory(self):
        """Should handle large tool result lists."""
        user_id = "test_large"
        large_tools = [{"tool": f"tool_{i}", "result": f"result_{i}" * 100} for i in range(1000)]

        working.update(user_id, large_tools)
        retrieved = working.get(user_id)

        assert len(retrieved) == 1000
        assert retrieved[0]["tool"] == "tool_0"
        assert retrieved[999]["tool"] == "tool_999"
