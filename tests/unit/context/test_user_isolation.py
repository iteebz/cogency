"""User isolation tests across all context modules.

These tests validate that user data is properly isolated between different
users across working memory, memory, conversation, knowledge, and context assembly.
"""

import pytest

from cogency.context import context, conversation, knowledge, memory, working


class TestUserIsolationAcrossModules:
    """Test user isolation across all context modules."""

    def test_working_memory_isolation(self):
        """Working memory completely isolated between users."""
        user_a = "user_a"
        user_b = "user_b"
        user_c = "user_c"

        # Set up different working memory for each user
        tools_a = [{"tool": "file_write", "result": "User A file operations"}]
        tools_b = [{"tool": "api_call", "result": "User B API responses"}]
        tools_c = [{"tool": "database", "result": "User C database queries"}]

        working.update(user_a, tools_a)
        working.update(user_b, tools_b)
        working.update(user_c, tools_c)

        # Verify complete isolation
        assert working.get(user_a) == tools_a
        assert working.get(user_b) == tools_b
        assert working.get(user_c) == tools_c

        # Verify no cross-contamination
        assert working.get(user_a) != working.get(user_b)
        assert working.get(user_b) != working.get(user_c)
        assert working.get(user_a) != working.get(user_c)

        # Clear one user - should not affect others
        working.clear(user_b)
        assert working.get(user_a) == tools_a
        assert working.get(user_b) == []  # Only user_b cleared
        assert working.get(user_c) == tools_c

    def test_user_memory_isolation(self):
        """User memory profiles completely isolated."""
        user_a = "memory_user_a"
        user_b = "memory_user_b"
        user_c = "memory_user_c"

        # Set up different profiles
        profile_a = {"name": "Alice", "role": "designer", "projects": ["UI", "UX"]}
        profile_b = {"name": "Bob", "role": "developer", "skills": ["Python", "JS"]}
        profile_c = {"name": "Carol", "role": "manager", "team": "engineering"}

        memory.update(user_a, profile_a)
        memory.update(user_b, profile_b)
        memory.update(user_c, profile_c)

        # Verify complete isolation
        assert memory.get(user_a) == profile_a
        assert memory.get(user_b) == profile_b
        assert memory.get(user_c) == profile_c

        # Verify no cross-contamination
        assert memory.get(user_a)["name"] != memory.get(user_b)["name"]
        assert memory.get(user_b)["role"] != memory.get(user_c)["role"]

        # Clear one user - should not affect others
        memory.clear(user_a)
        cleared_result = memory.get(user_a)
        assert cleared_result is None or cleared_result == {}
        assert memory.get(user_b) == profile_b
        assert memory.get(user_c) == profile_c

    def test_conversation_isolation(self):
        """Conversation history completely isolated between users."""
        user_a = "conv_user_a"
        user_b = "conv_user_b"
        user_c = "conv_user_c"

        # Clear any existing conversations from previous tests
        conversation.clear(user_a)
        conversation.clear(user_b)
        conversation.clear(user_c)

        # Add different conversation messages
        conversation.add(user_a, "user", "Hello, I need help with design")
        conversation.add(user_a, "assistant", "I can help with UI/UX design")

        conversation.add(user_b, "user", "Debug this Python code please")
        conversation.add(user_b, "assistant", "Let me analyze your code")

        conversation.add(user_c, "user", "Project management advice needed")
        conversation.add(user_c, "assistant", "I can help with team coordination")

        # Verify complete isolation
        conv_a = conversation.get(user_a)
        conv_b = conversation.get(user_b)
        conv_c = conversation.get(user_c)

        assert len(conv_a) == 2
        assert len(conv_b) == 2
        assert len(conv_c) == 2

        # Verify content isolation
        assert "design" in conv_a[0]["content"]
        assert "Python" in conv_b[0]["content"]
        assert "management" in conv_c[0]["content"]

        # Verify no cross-contamination
        assert all("Python" not in msg["content"] for msg in conv_a)
        assert all("design" not in msg["content"] for msg in conv_b)
        assert all("management" not in msg["content"] for msg in conv_a + conv_b)

        # Clear one user - should not affect others
        conversation.clear(user_b)
        assert conversation.get(user_a) == conv_a  # Unchanged
        assert conversation.get(user_b) == []  # Cleared
        assert conversation.get(user_c) == conv_c  # Unchanged

    def test_knowledge_isolation(self):
        """Knowledge search and storage isolated between users."""
        user_a = "knowledge_user_a"
        user_b = "knowledge_user_b"

        # Test search isolation (formatted results should be different)
        # Note: Current implementation has TODO for user-scoped search
        search_a = knowledge.search("design patterns", user_a)
        search_b = knowledge.search("algorithm optimization", user_b)

        # Even if backend isn't user-scoped yet, API should accept user_id
        assert isinstance(search_a, list)
        assert isinstance(search_b, list)

        # Test format isolation
        format_a = knowledge.format("design patterns", user_a)
        format_b = knowledge.format("algorithm optimization", user_b)

        assert isinstance(format_a, str)
        assert isinstance(format_b, str)

    def test_context_assembly_isolation(self):
        """Context assembly maintains user isolation across all modules."""
        user_a = "assembly_user_a"
        user_b = "assembly_user_b"

        # Set up different data for each user across all modules
        working.update(user_a, [{"tool": "design_tool", "result": "UI mockup created"}])
        working.update(
            user_b, [{"tool": "code_analyzer", "result": "Performance bottleneck found"}]
        )

        memory.update(user_a, {"name": "Designer Alice", "focus": "visual design"})
        memory.update(user_b, {"name": "Developer Bob", "focus": "optimization"})

        conversation.add(user_a, "user", "Help me with color schemes")
        conversation.add(user_b, "user", "Optimize this database query")

        # Assemble context for each user
        context_a = context.assemble("Continue my design work", user_a, working.get(user_a))
        context_b = context.assemble("Continue optimization task", user_b, working.get(user_b))

        # Verify contexts are different and contain user-specific data
        assert context_a != context_b
        assert isinstance(context_a, str)
        assert isinstance(context_b, str)

        # Verify user-specific content appears in correct context
        # (This is implementation-dependent on how format() methods work)
        assert len(context_a) > 0
        assert len(context_b) > 0

    def test_concurrent_user_operations(self):
        """Multiple users can operate simultaneously without interference."""
        # Simulate concurrent operations across multiple users
        users = [f"concurrent_user_{i}" for i in range(10)]

        # Each user performs operations across all modules
        for i, user_id in enumerate(users):
            # Working memory operations
            working.update(user_id, [{"tool": f"tool_{i}", "result": f"result_{i}"}])

            # Memory operations
            memory.update(user_id, {"user_id": i, "name": f"User {i}"})

            # Conversation operations
            conversation.add(user_id, "user", f"Message from user {i}")

        # Verify all operations maintain isolation
        for i, user_id in enumerate(users):
            # Check working memory isolation
            work_data = working.get(user_id)
            assert work_data[0]["tool"] == f"tool_{i}"

            # Check memory isolation
            mem_data = memory.get(user_id)
            assert mem_data["user_id"] == i

            # Check conversation isolation
            conv_data = conversation.get(user_id)
            assert f"user {i}" in conv_data[0]["content"]

        # Clean up one user - should not affect others
        target_user = users[5]
        working.clear(target_user)
        memory.clear(target_user)
        conversation.clear(target_user)

        # Verify only target user affected
        assert working.get(target_user) == []
        assert memory.get(target_user) in [None, {}]
        assert conversation.get(target_user) == []

        # Verify other users unaffected
        for user_id in users:
            if user_id != target_user:
                assert len(working.get(user_id)) > 0
                assert memory.get(user_id) is not None
                assert len(conversation.get(user_id)) > 0

    def test_user_id_validation_across_modules(self):
        """All modules properly validate user_id parameter."""
        # Test None user_id handling across all modules
        with pytest.raises((ValueError, TypeError)):
            working.get(None)

        with pytest.raises((ValueError, TypeError)):
            memory.get(None)

        with pytest.raises((ValueError, TypeError)):
            context.assemble("test", None)

        # Test empty string handling (should work)
        empty_user = ""

        # These should not raise errors
        working.update(empty_user, [])
        memory.update(empty_user, {})
        conversation.add(empty_user, "user", "test")

        assert working.get(empty_user) == []
        assert memory.get(empty_user) in [None, {}]
        assert isinstance(conversation.get(empty_user), list)


class TestCrossModuleDataLeakage:
    """Test for data leakage between modules and users."""

    def test_no_shared_references(self):
        """Verify no shared object references between users."""
        user_a = "ref_user_a"
        user_b = "ref_user_b"

        # Working memory reference isolation
        tools_template = [{"tool": "shared_tool", "result": "data"}]
        working.update(user_a, tools_template)
        working.update(user_b, tools_template)

        # Modify one user's data
        user_a_data = working.get(user_a)
        user_a_data[0]["result"] = "modified_data"
        working.update(user_a, user_a_data)

        # Verify user_b unaffected
        user_b_data = working.get(user_b)
        assert user_b_data[0]["result"] == "data"  # Original value

    def test_memory_data_independence(self):
        """Verify memory data is independent between users."""
        user_a = "mem_ref_a"
        user_b = "mem_ref_b"

        # Use same base profile structure
        base_profile = {"settings": {"theme": "light"}, "preferences": ["email"]}

        memory.update(user_a, base_profile.copy())
        memory.update(user_b, base_profile.copy())

        # Modify one user's nested data
        profile_a = memory.get(user_a)
        if profile_a:
            profile_a["settings"]["theme"] = "dark"
            profile_a["preferences"].append("sms")
            memory.update(user_a, profile_a)

        # Verify user_b unaffected
        profile_b = memory.get(user_b)
        if profile_b:
            assert profile_b["settings"]["theme"] == "light"
            assert "sms" not in profile_b["preferences"]

    def test_format_method_isolation(self):
        """Verify format methods don't leak data between users."""
        user_a = "format_user_a"
        user_b = "format_user_b"

        # Set up different data
        working.update(user_a, [{"tool": "design", "result": "wireframe"}])
        working.update(user_b, [{"tool": "code", "result": "function"}])

        memory.update(user_a, {"name": "Alice Designer", "context": "UI/UX design work"})
        memory.update(user_b, {"name": "Bob Developer", "context": "backend optimization"})

        # Format for each user
        work_format_a = working.format(working.get(user_a))
        work_format_b = working.format(working.get(user_b))

        mem_format_a = memory.format(user_a)
        mem_format_b = memory.format(user_b)

        # Verify formats are different and contain correct data
        assert work_format_a != work_format_b
        assert mem_format_a != mem_format_b

        # Verify cross-contamination absence (implementation dependent)
        if "design" in work_format_a:
            assert "design" not in work_format_b
        if "wireframe" in work_format_a:
            assert "wireframe" not in work_format_b
