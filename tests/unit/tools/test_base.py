"""Tool base tests - essential interface and validation tests."""

from dataclasses import dataclass

import pytest
from resilient_result import Result

from cogency.tools.base import Tool
from cogency.tools.files import Files


@dataclass
class DummyArgs:
    query: str
    max_results: int = 5


class DummyTool(Tool):
    def __init__(self):
        super().__init__(
            name="test_tool",
            description="Tool for testing",
            schema="test_tool(query: str, max_results: int = 5)",
            args=DummyArgs,
        )

    async def run(self, query: str, max_results: int = 5, **kwargs) -> Result:
        return Result.ok({"query": query, "max_results": max_results})


@pytest.mark.asyncio
async def test_interface():
    """Test tool interface contracts."""
    tool = Files()

    assert hasattr(tool, "name")
    assert hasattr(tool, "description")
    assert tool.name == "files"

    assert hasattr(tool, "run")
    assert hasattr(tool, "schema")
    assert hasattr(tool, "examples")

    schema = tool.schema
    examples = tool.examples

    assert isinstance(schema, str) and len(schema) > 0
    assert isinstance(examples, list) and len(examples) > 0


@pytest.mark.asyncio
async def test_validation_errors():
    """Test argument validation logic."""
    tool = DummyTool()

    # Test invalid argument
    result = await tool.execute(invalid_arg="test")
    assert result.failure
    assert "validation failed" in result.error.lower()


@pytest.mark.asyncio
async def test_missing_required():
    """Test required argument validation."""
    tool = DummyTool()

    # Test missing required argument
    result = await tool.execute(max_results=5)  # Missing 'query'
    assert result.failure
    assert "validation failed" in result.error.lower()


@pytest.mark.asyncio
async def test_valid_args():
    """Test that valid arguments work correctly."""
    tool = DummyTool()

    result = await tool.execute(query="test query", max_results=10)
    assert result.success
    assert result.data["query"] == "test query"
    assert result.data["max_results"] == 10


class NoSchemaTool(Tool):
    """Tool without dataclass schema for testing."""

    def __init__(self):
        super().__init__(
            name="no_schema", description="Tool without schema", schema="no_schema(value='test')"
        )

    async def run(self, **kwargs):
        return Result.ok({"value": kwargs.get("value", "default")})


@pytest.mark.asyncio
async def test_no_schema():
    """Test tool execution without dataclass validation."""
    tool = NoSchemaTool()

    result = await tool.execute(value="test_value")
    assert result.success
    assert result.data["value"] == "test_value"


class RawReturnTool(Tool):
    """Tool that returns raw values for auto-wrapping."""

    def __init__(self):
        super().__init__(
            name="raw_return", description="Returns raw values", schema="raw_return(data='test')"
        )

    async def run(self, **kwargs):
        return kwargs.get("data", "raw_result")


@pytest.mark.asyncio
async def test_result_wrapping():
    """Test execute auto-wraps non-Result returns."""
    tool = RawReturnTool()

    result = await tool.execute(data="test_data")
    assert result.success
    assert result.data == "test_data"


@pytest.mark.asyncio
async def test_error_handling():
    """Test execute handles runtime errors gracefully."""

    class ErrorTool(Tool):
        def __init__(self):
            super().__init__(
                name="error_tool", description="Tool that errors", schema="error_tool()"
            )

        async def run(self, **kwargs):
            raise Exception("Execution failed")

    tool = ErrorTool()
    result = await tool.execute()

    assert result.failure
    assert "Tool execution failed" in result.error


def test_initialization():
    """Test comprehensive tool initialization."""
    tool = DummyTool()

    assert tool.name == "test_tool"
    assert tool.description == "Tool for testing"
    assert tool.schema == "test_tool(query: str, max_results: int = 5)"
    assert tool.args == DummyArgs
    assert tool.emoji == "🛠️"  # Default
    assert tool.examples == []  # Default
    assert tool.rules == []  # Default


def test_custom_properties():
    """Test tool with custom properties."""

    class CustomTool(Tool):
        def __init__(self):
            super().__init__(
                name="custom",
                description="Custom tool",
                schema="custom(arg='value')",
                emoji="🎯",
                examples=["custom(arg='example')"],
                rules=["Use with caution"],
            )

        async def run(self, **kwargs):
            return Result.ok({})

    tool = CustomTool()
    assert tool.emoji == "🎯"
    assert tool.examples == ["custom(arg='example')"]
    assert tool.rules == ["Use with caution"]


def test_format_args():
    """Test argument formatting for display."""
    tool = DummyTool()

    # Test basic formatting
    formatted = tool._format_args({"query": "test", "max_results": 5})
    assert "test" in formatted or "5" in formatted

    # Test empty args
    formatted = tool._format_args({})
    assert formatted == ""


def test_format_result():
    """Test result formatting for display."""
    tool = DummyTool()

    # Test standard result format
    formatted = tool._format_result({"result": "success"})
    assert formatted == "success"

    # Test message format
    formatted = tool._format_result({"message": "completed"})
    assert formatted == "completed"

    # Test empty result
    formatted = tool._format_result({})
    assert formatted == "Completed"


def test_human_formatting():
    """Test human-readable formatting."""
    tool = DummyTool()
    args = {"query": "test"}

    # Test with no results
    arg_str, result_str = tool.format_human(args)
    assert result_str == ""

    # Test with success result
    success_result = Result.ok({"result": "success"})
    arg_str, result_str = tool.format_human(args, success_result)
    assert result_str == "success"

    # Test with failure result
    fail_result = Result.fail("error occurred")
    arg_str, result_str = tool.format_human(args, fail_result)
    assert "Error: error occurred" in result_str


def test_agent_formatting():
    """Test agent-readable formatting."""
    tool = DummyTool()

    # Test standard result
    formatted = tool.format_agent({"result": "agent_result"})
    assert formatted == "agent_result"

    # Test empty result
    formatted = tool.format_agent({})
    assert formatted == "No result"


def test_arg_normalization():
    """Test argument normalization."""
    tool = DummyTool()
    original_args = {"key": "value", "number": 42}

    normalized = tool._normalize_args(original_args)
    assert normalized == original_args  # Base implementation returns unchanged
