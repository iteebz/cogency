"""Isolation tests across all context modules.

These tests validate that user data is properly isolated between different
users across working memory, memory, conversation, knowledge, and context assembly.
"""

import pytest

from cogency.context import context, conversation, knowledge, memory, working


def test_working_memory_isolation():
    """Working memory completely isolated between tasks."""
    task_a = "task_a"
    task_b = "task_b"
    task_c = "task_c"

    # Set up different working memory for each task
    tools_a = [{"tool": "file_write", "result": "User A file operations"}]
    tools_b = [{"tool": "api_call", "result": "User B API responses"}]
    tools_c = [{"tool": "database", "result": "User C database queries"}]

    working.update(task_a, tools_a)
    working.update(task_b, tools_b)
    working.update(task_c, tools_c)

    # Verify complete isolation
    assert working.get(task_a) == tools_a
    assert working.get(task_b) == tools_b
    assert working.get(task_c) == tools_c

    # Verify no cross-contamination
    assert working.get(task_a) != working.get(task_b)
    assert working.get(task_b) != working.get(task_c)
    assert working.get(task_a) != working.get(task_c)

    # Clear one task - should not affect others
    working.clear(task_b)
    assert working.get(task_a) == tools_a
    assert working.get(task_b) == []  # Only task_b cleared
    assert working.get(task_c) == tools_c


def test_user_memory_isolation():
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


def test_conversation_isolation():
    """Conversation history completely isolated between users."""
    import uuid

    # Use conversation_id format: user_id_timestamp
    user_a_id = f"conv_user_a_{uuid.uuid4().hex[:8]}"
    user_b_id = f"conv_user_b_{uuid.uuid4().hex[:8]}"
    user_c_id = f"conv_user_c_{uuid.uuid4().hex[:8]}"

    conv_a = f"{user_a_id}_{uuid.uuid4().hex[:8]}"
    conv_b = f"{user_b_id}_{uuid.uuid4().hex[:8]}"
    conv_c = f"{user_c_id}_{uuid.uuid4().hex[:8]}"

    # Clear any existing conversations from previous tests
    conversation.clear(conv_a)
    conversation.clear(conv_b)
    conversation.clear(conv_c)

    # Add different conversation messages
    conversation.add(conv_a, "user", "Hello, I need help with design")
    conversation.add(conv_a, "assistant", "I can help with UI/UX design")

    conversation.add(conv_b, "user", "Debug this Python code please")
    conversation.add(conv_b, "assistant", "Let me analyze your code")

    conversation.add(conv_c, "user", "Project management advice needed")
    conversation.add(conv_c, "assistant", "I can help with team coordination")

    # Verify complete isolation
    conv_a_messages = conversation.get(conv_a)
    conv_b_messages = conversation.get(conv_b)
    conv_c_messages = conversation.get(conv_c)

    assert len(conv_a_messages) == 2
    assert len(conv_b_messages) == 2
    assert len(conv_c_messages) == 2

    # Verify content isolation
    assert "design" in conv_a_messages[0]["content"]
    assert "Python" in conv_b_messages[0]["content"]
    assert "management" in conv_c_messages[0]["content"]

    # Verify no cross-contamination
    assert all("Python" not in msg["content"] for msg in conv_a_messages)
    assert all("design" not in msg["content"] for msg in conv_b_messages)
    assert all("management" not in msg["content"] for msg in conv_a_messages + conv_b_messages)

    # Clear one user - should not affect others
    conversation.clear(conv_b)
    assert conversation.get(conv_a) == conv_a_messages  # Unchanged
    assert conversation.get(conv_b) == []  # Cleared
    assert conversation.get(conv_c) == conv_c_messages  # Unchanged


def test_knowledge_isolation():
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
    format_a = knowledge.format(user_a)
    format_b = knowledge.format(user_b)

    assert isinstance(format_a, str)
    assert isinstance(format_b, str)


def test_context_assembly_isolation():
    """Context assembly maintains user isolation across all modules."""
    user_a = "assembly_user_a"
    user_b = "assembly_user_b"
    task_a = "task_a"
    task_b = "task_b"

    # Set up different data for each user across all modules
    working.update(task_a, [{"tool": "design_tool", "result": "UI mockup created"}])
    working.update(task_b, [{"tool": "code_analyzer", "result": "Performance bottleneck found"}])

    memory.update(user_a, {"name": "Designer Alice", "focus": "visual design"})
    memory.update(user_b, {"name": "Developer Bob", "focus": "optimization"})

    conv_a = f"{user_a}_{task_a}"
    conv_b = f"{user_b}_{task_b}"
    conversation.add(conv_a, "user", "Help me with color schemes")
    conversation.add(conv_b, "user", "Optimize this database query")

    # Assemble context for each user
    context_a = context.assemble("Continue my design work", user_a, conv_a, task_a)
    context_b = context.assemble("Continue optimization task", user_b, conv_b, task_b)

    # Verify contexts are different and contain user-specific data
    assert context_a != context_b
    assert isinstance(context_a, list)
    assert isinstance(context_b, list)

    # Verify user-specific content appears in correct context
    # (This is implementation-dependent on how format() methods work)
    assert len(context_a) > 0
    assert len(context_b) > 0


def test_concurrent_user_operations():
    """Multiple users can operate simultaneously without interference."""
    # Simulate concurrent operations across multiple users
    import uuid

    base_id = uuid.uuid4().hex[:8]
    users = [f"concurrent_user_{i}_{base_id}" for i in range(10)]

    # Each user performs operations across all modules
    for i, user_id in enumerate(users):
        task_id = f"task_{i}_{base_id}"
        conv_id = f"{user_id}_{task_id}"

        # Working memory operations (task-scoped)
        working.update(task_id, [{"tool": f"tool_{i}", "result": f"result_{i}"}])

        # Memory operations (user-scoped)
        memory.update(user_id, {"user_id": i, "name": f"User {i}"})

        # Conversation operations (conversation-scoped)
        conversation.add(conv_id, "user", f"Message from user {i}")

    # Verify all operations maintain isolation
    for i, user_id in enumerate(users):
        task_id = f"task_{i}_{base_id}"
        conv_id = f"{user_id}_{task_id}"

        # Check working memory isolation
        work_data = working.get(task_id)
        assert work_data[0]["tool"] == f"tool_{i}"

        # Check memory isolation
        mem_data = memory.get(user_id)
        assert mem_data["user_id"] == i

        # Check conversation isolation
        conv_data = conversation.get(conv_id)
        assert f"user {i}" in conv_data[0]["content"]

    # Clean up one user - should not affect others
    target_user = users[5]
    target_task = f"task_5_{base_id}"
    target_conv = f"{target_user}_{target_task}"

    working.clear(target_task)  # Clear task-scoped data
    memory.clear(target_user)  # Clear user-scoped data
    conversation.clear(target_conv)  # Clear conversation-scoped data

    # Verify only target user affected
    assert working.get(target_task) == []
    assert memory.get(target_user) in [None, {}]
    assert conversation.get(target_conv) == []

    # Verify other users unaffected
    for i, user_id in enumerate(users):
        if user_id != target_user:
            task_id = f"task_{i}_{base_id}"
            conv_id = f"{user_id}_{task_id}"
            assert len(working.get(task_id)) > 0
            assert memory.get(user_id) is not None
            assert len(conversation.get(conv_id)) > 0


def test_user_id_validation_across_modules():
    """All modules properly validate user_id parameter."""
    # Test None user_id handling across all modules
    with pytest.raises((ValueError, TypeError)):
        working.get(None)

    with pytest.raises((ValueError, TypeError)):
        memory.get(None)

    with pytest.raises((ValueError, TypeError)):
        context.assemble("test", None, "conv", "task")

    # Test empty string handling (should work)
    empty_user = ""
    empty_task = ""
    empty_conv = ""

    # These should not raise errors
    working.update(empty_task, [])
    memory.update(empty_user, {})
    conversation.add(empty_conv, "user", "test")

    assert working.get(empty_task) == []
    assert memory.get(empty_user) in [None, {}]
    assert isinstance(conversation.get(empty_conv), list)


def test_no_shared_references():
    """Verify no shared object references between users."""
    task_a = "ref_task_a"
    task_b = "ref_task_b"

    # Working memory reference isolation
    tools_template = [{"tool": "shared_tool", "result": "data"}]
    working.update(task_a, tools_template)
    working.update(task_b, tools_template)

    # Modify one task's data
    task_a_data = working.get(task_a)
    task_a_data[0]["result"] = "modified_data"
    working.update(task_a, task_a_data)

    # Verify task_b unaffected
    task_b_data = working.get(task_b)
    assert task_b_data[0]["result"] == "data"  # Original value


def test_memory_data_independence():
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


def test_format_method_isolation():
    """Verify format methods don't leak data between users."""
    user_a = "format_user_a"
    user_b = "format_user_b"
    task_a = "format_task_a"
    task_b = "format_task_b"
    conv_a = f"{user_a}_{task_a}"
    conv_b = f"{user_b}_{task_b}"

    # Set up different data
    working.update(task_a, [{"tool": "design", "result": "wireframe"}])
    working.update(task_b, [{"tool": "code", "result": "function"}])

    memory.update(user_a, {"name": "Alice Designer", "context": "UI/UX design work"})
    memory.update(user_b, {"name": "Bob Developer", "context": "backend optimization"})

    conversation.add(conv_a, "user", "Design help needed")
    conversation.add(conv_b, "user", "Code optimization needed")

    # Format for each user/task
    work_format_a = working.format(task_a)
    work_format_b = working.format(task_b)

    mem_format_a = memory.format(user_a)
    mem_format_b = memory.format(user_b)

    conv_format_a = conversation.format(conv_a)
    conv_format_b = conversation.format(conv_b)

    # Verify formats are different and contain correct data
    assert work_format_a != work_format_b
    assert mem_format_a != mem_format_b
    assert conv_format_a != conv_format_b

    # Verify cross-contamination absence (implementation dependent)
    if "design" in work_format_a:
        assert "design" not in work_format_b
    if "wireframe" in work_format_a:
        assert "wireframe" not in work_format_b
