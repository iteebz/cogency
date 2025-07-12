from cogency.context import Context


class TestContext:
    def test_init_default(self):
        """Test Context initialization with defaults."""
        context = Context("test input")
        assert context.current_input == "test input"
        assert context.messages == []
        assert context.tool_results == []
        assert context.max_history is None

    def test_init_with_max_history(self):
        """Test Context initialization with max_history."""
        context = Context("test input", max_history=5)
        assert context.max_history == 5

    def test_add_message_basic(self):
        """Test basic message addition."""
        context = Context("test input")
        context.add_message("user", "hello")
        context.add_message("assistant", "hi there")

        assert len(context.messages) == 2
        assert context.messages[0] == {"role": "user", "content": "hello"}
        assert context.messages[1] == {"role": "assistant", "content": "hi there"}

    def test_add_message_with_sliding_window(self):
        """Test message addition with sliding window."""
        context = Context("test input", max_history=3)

        # Add messages up to limit
        context.add_message("user", "msg1")
        context.add_message("assistant", "msg2")
        context.add_message("user", "msg3")
        assert len(context.messages) == 3

        # Add one more - should trigger sliding window
        context.add_message("assistant", "msg4")
        assert len(context.messages) == 3
        assert context.messages[0]["content"] == "msg2"  # First message was dropped
        assert context.messages[1]["content"] == "msg3"
        assert context.messages[2]["content"] == "msg4"

    def test_add_message_with_trace(self):
        """Test add_message_with_trace functionality."""
        context = Context("test input")
        context.add_message_with_trace("user", "hello", "trace123")

        assert len(context.messages) == 1
        assert context.messages[0] == {"role": "user", "content": "hello", "trace_id": "trace123"}

    def test_add_message_with_trace_sliding_window(self):
        """Test add_message_with_trace with sliding window."""
        context = Context("test input", max_history=2)

        context.add_message_with_trace("user", "msg1", "trace1")
        context.add_message_with_trace("assistant", "msg2", "trace2")
        context.add_message_with_trace("user", "msg3", "trace3")

        assert len(context.messages) == 2
        assert context.messages[0]["content"] == "msg2"
        assert context.messages[1]["content"] == "msg3"

    def test_sliding_window_edge_cases(self):
        """Test edge cases for sliding window."""
        # max_history = 1
        context = Context("test", max_history=1)
        context.add_message("user", "first")
        context.add_message("assistant", "second")

        assert len(context.messages) == 1
        assert context.messages[0]["content"] == "second"

        # max_history = 0 (should not crash)
        context = Context("test", max_history=0)
        context.add_message("user", "msg")
        assert len(context.messages) == 0

    def test_no_sliding_window_when_max_history_none(self):
        """Test that sliding window doesn't activate when max_history is None."""
        context = Context("test input")  # max_history=None by default

        # Add many messages
        for i in range(100):
            context.add_message("user", f"message {i}")

        assert len(context.messages) == 100

    def test_get_clean_conversation(self):
        """Test that get_clean_conversation works with sliding window."""
        context = Context("test", max_history=3)

        context.add_message("user", "hello")
        context.add_message("assistant", "hi")
        context.add_message("system", "internal message")  # Should be filtered
        context.add_message("user", "how are you?")  # Should trigger sliding window

        clean = context.get_clean_conversation()
        # System message filtered out, and sliding window applied
        assert len(clean) == 2
        assert clean[0]["content"] == "hi"
        assert clean[1]["content"] == "how are you?"
