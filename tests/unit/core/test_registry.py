import pytest

from cogency.core.protocols import Tool
from cogency.core.registry import ToolRegistry


def test_register(mock_tool, mock_storage):
    registry = ToolRegistry(mock_storage)
    initial_count = len(registry.by_name)

    mock_a = mock_tool(name="mock_a")
    registry.register(mock_a, "test")
    assert "mock_a" in registry.by_name
    assert len(registry.by_name) == initial_count + 1


def test_register_duplicate(mock_tool, mock_storage):
    registry = ToolRegistry(mock_storage)
    mock_a = mock_tool(name="mock_a")
    registry.register(mock_a, "test")
    with pytest.raises(ValueError, match="already registered"):
        registry.register(mock_a, "test")


def test_register_invalid(mock_storage):
    registry = ToolRegistry(mock_storage)
    with pytest.raises(ValueError):
        registry.register("not a tool", "test")  # type: ignore[arg-type]


def test_category(mock_tool, mock_storage):
    registry = ToolRegistry(mock_storage)
    mock_a = mock_tool(name="mock_a")
    mock_b = mock_tool(name="mock_b")
    registry.register(mock_a, "cat1")
    registry.register(mock_b, "cat2")

    cat1_tools = registry.category("cat1")
    assert len(cat1_tools) == 1
    assert cat1_tools[0].name == "mock_a"

    multi_tools = registry.category(["cat1", "cat2"])
    assert len(multi_tools) == 2


def test_name(mock_tool, mock_storage):
    registry = ToolRegistry(mock_storage)
    mock_a = mock_tool(name="mock_a")
    mock_b = mock_tool(name="mock_b")
    registry.register(mock_a, "test")
    registry.register(mock_b, "test")

    tools = registry.name("mock_a")
    assert len(tools) == 1
    assert tools[0].name == "mock_a"

    multi_tools = registry.name(["mock_a", "mock_b"])
    assert len(multi_tools) == 2


def test_get(mock_tool, mock_storage):
    registry = ToolRegistry(mock_storage)
    mock_a = mock_tool(name="mock_a")
    registry.register(mock_a, "test")

    tool = registry.get("mock_a")
    assert tool is not None
    assert tool.name == "mock_a"

    missing = registry.get("nonexistent")
    assert missing is None


def test_call(mock_storage):
    registry = ToolRegistry(mock_storage)
    all_tools = registry()
    assert len(all_tools) > 0
    assert all(isinstance(t, Tool) for t in all_tools)
