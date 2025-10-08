import pytest

from cogency.core.protocols import Tool, ToolResult
from cogency.tools.registry import ToolRegistry


class MockA(Tool):
    name = "mock_a"
    description = "Mock A"

    def describe(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "schema": {},
        }

    async def execute(self, **kwargs):
        return ToolResult(outcome="a")


class MockB(Tool):
    name = "mock_b"
    description = "Mock B"

    def describe(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "schema": {},
        }

    async def execute(self, **kwargs):
        return ToolResult(outcome="b")


def test_register():
    registry = ToolRegistry()
    initial_count = len(registry.by_name)

    registry.register(MockA(), "test")
    assert "mock_a" in registry.by_name
    assert len(registry.by_name) == initial_count + 1


def test_register_duplicate():
    registry = ToolRegistry()
    registry.register(MockA(), "test")
    with pytest.raises(ValueError, match="already registered"):
        registry.register(MockA(), "test")


def test_register_invalid():
    registry = ToolRegistry()
    with pytest.raises(TypeError):
        registry.register("not a tool", "test")


def test_category():
    registry = ToolRegistry()
    registry.register(MockA(), "cat1")
    registry.register(MockB(), "cat2")

    cat1_tools = registry.category("cat1")
    assert len(cat1_tools) == 1
    assert cat1_tools[0].name == "mock_a"

    multi_tools = registry.category(["cat1", "cat2"])
    assert len(multi_tools) == 2


def test_name():
    registry = ToolRegistry()
    registry.register(MockA(), "test")
    registry.register(MockB(), "test")

    tools = registry.name("mock_a")
    assert len(tools) == 1
    assert tools[0].name == "mock_a"

    multi_tools = registry.name(["mock_a", "mock_b"])
    assert len(multi_tools) == 2


def test_get():
    registry = ToolRegistry()
    registry.register(MockA(), "test")

    tool = registry.get("mock_a")
    assert tool.name == "mock_a"

    missing = registry.get("nonexistent")
    assert missing is None


def test_call():
    registry = ToolRegistry()
    all_tools = registry()
    assert len(all_tools) > 0
    assert all(isinstance(t, Tool) for t in all_tools)
