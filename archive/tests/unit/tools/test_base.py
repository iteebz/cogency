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
    """Test basic tool interface requirements."""
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
    """Test argument validation error handling."""
    tool = DummyTool()

    # Test invalid argument
    result = await tool.execute(invalid_arg="test")
    assert result.failure
    assert "validation failed" in result.error.lower()


@pytest.mark.asyncio
async def test_missing_required():
    """Test handling of missing required arguments."""
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
