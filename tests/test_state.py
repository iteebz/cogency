"""Test State contracts and behavior."""

from cogency.output import Output
from cogency.state import State


class TestState:
    """Test State behavior and contracts."""

    def test_state_creation(self, context):
        state = State(context=context, query="test query", output=Output())

        assert state["context"] == context
        assert state["query"] == "test query"
        assert isinstance(state["output"], Output)

    def test_dict_access(self, context):
        """State should behave like a dict for backward compatibility."""
        state = State(context=context, query="test query", output=Output())

        # Test dict-like access
        assert "context" in state
        assert "query" in state
        assert "output" in state

        # Test getting items
        assert state.get("context") == context
        assert state.get("nonexistent") is None

        # Test updating
        state["new_field"] = "test_value"
        assert state["new_field"] == "test_value"
