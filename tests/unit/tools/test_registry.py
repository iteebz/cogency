"""Tool registry tests."""

from cogency.tools.base import Tool
from cogency.tools.registry import ToolRegistry, tool


@tool
class DummyTool(Tool):
    def __init__(self):
        super().__init__(
            name="dummy",
            description="Test tool",
            schema="dummy()",
            args=None,
        )

    async def run(self, **kwargs):
        return {"result": "success"}


def test_decorator_registration():
    """Test tool decorator registers tool class."""
    ToolRegistry.clear()

    @tool
    class TestTool(Tool):
        def __init__(self):
            super().__init__(name="test", description="Test", schema="test()", args=None)

        async def run(self, **kwargs):
            return {"result": "test"}

    tools = ToolRegistry.get_tools()
    assert len(tools) == 1
    assert tools[0].name == "test"


def test_instance_creation():
    """Test getting all registered tool instances."""
    ToolRegistry.clear()
    ToolRegistry.add(DummyTool)

    tools = ToolRegistry.get_tools()
    assert isinstance(tools, list)
    assert len(tools) == 1
    assert tools[0].name == "dummy"


def test_registry_reset():
    """Test clearing registry state."""
    ToolRegistry.add(DummyTool)
    tools = ToolRegistry.get_tools()
    assert len(tools) > 0

    ToolRegistry.clear()
    tools = ToolRegistry.get_tools()
    assert len(tools) == 0


def test_deduplication():
    """Test duplicate registration deduplication logic."""
    ToolRegistry.clear()

    ToolRegistry.add(DummyTool)
    ToolRegistry.add(DummyTool)  # Add same class again

    tools = ToolRegistry.get_tools()
    assert len(tools) == 1  # Should only have one instance


def test_thread_safety():
    """Test registry thread safety with concurrent operations."""
    import threading

    ToolRegistry.clear()
    results = []

    def register_tool():
        ToolRegistry.add(DummyTool)
        tools = ToolRegistry.get_tools()
        results.append(len(tools))

    threads = [threading.Thread(target=register_tool) for _ in range(5)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # Should have consistent results despite concurrent access
    final_tools = ToolRegistry.get_tools()
    assert len(final_tools) == 1  # Deduplication should work


def test_registry_isolation():
    """Test registry operations don't affect each other."""
    # Clear and setup initial state
    ToolRegistry.clear()
    assert len(ToolRegistry.get_tools()) == 0

    # Add tool and verify
    ToolRegistry.add(DummyTool)
    assert len(ToolRegistry.get_tools()) == 1

    # Clear should reset state completely
    ToolRegistry.clear()
    assert len(ToolRegistry.get_tools()) == 0

    # Re-adding should work normally
    ToolRegistry.add(DummyTool)
    assert len(ToolRegistry.get_tools()) == 1
