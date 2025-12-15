from dataclasses import dataclass
from typing import Annotated

import pytest

from cogency.core.protocols import ToolParam, ToolResult
from cogency.core.tool import tool


@dataclass
class MinimalParams:
    message: str


@dataclass
class AnnotatedParams:
    required: Annotated[str, ToolParam(description="Required field")]
    optional: Annotated[int, ToolParam(description="Optional field")] = 42


@dataclass
class BoundedParams:
    count: Annotated[int, ToolParam(description="Count", ge=1, le=100)]
    text: Annotated[str, ToolParam(description="Text", min_length=1, max_length=200)]


def test_tool_decorator_creates_instance():
    @tool("Test tool")
    async def test_func(params: MinimalParams) -> ToolResult:
        return ToolResult(outcome="ok")

    assert test_func.name == "test_func"
    assert test_func.description == "Test tool"


def test_schema_extraction_basic():
    @tool("Test")
    async def test_func(params: MinimalParams) -> ToolResult:
        return ToolResult(outcome="ok")

    assert "message" in test_func.schema
    assert test_func.schema["message"]["type"] == "string"
    assert test_func.schema["message"]["required"] is True


def test_schema_extraction_with_descriptions():
    @tool("Test")
    async def test_func(params: AnnotatedParams) -> ToolResult:
        return ToolResult(outcome="ok")

    assert test_func.schema["required"]["description"] == "Required field"
    assert test_func.schema["required"]["required"] is True
    assert test_func.schema["optional"]["description"] == "Optional field"
    assert test_func.schema["optional"]["required"] is False
    assert test_func.schema["optional"]["default"] == 42


def test_schema_extraction_with_bounds():
    @tool("Test")
    async def test_func(params: BoundedParams) -> ToolResult:
        return ToolResult(outcome="ok")

    assert test_func.schema["count"]["min"] == 1
    assert test_func.schema["count"]["max"] == 100
    assert test_func.schema["text"]["min_length"] == 1
    assert test_func.schema["text"]["max_length"] == 200


@pytest.mark.asyncio
async def test_execute_passes_params():
    @tool("Test")
    async def test_func(params: MinimalParams) -> ToolResult:
        return ToolResult(outcome=params.message)

    result = await test_func.execute(message="hello")
    assert result.outcome == "hello"


@pytest.mark.asyncio
async def test_execute_passes_extra_kwargs():
    @tool("Test")
    async def test_func(params: MinimalParams, storage=None) -> ToolResult:
        return ToolResult(outcome=f"{params.message}:{storage}")

    result = await test_func.execute(message="test", storage="db")
    assert result.outcome == "test:db"


def test_describe_with_args():
    @tool("Test")
    async def test_func(params: MinimalParams) -> ToolResult:
        return ToolResult(outcome="ok")

    assert test_func.describe({"message": "hello"}) == "test_func(message=hello)"


def test_describe_without_args():
    @tool("Test")
    async def test_func(params: MinimalParams) -> ToolResult:
        return ToolResult(outcome="ok")

    assert test_func.describe({}) == "test_func()"


def test_decorator_rejects_non_dataclass():
    with pytest.raises(TypeError, match="must be a dataclass"):

        @tool("Test")
        async def test_func(params: str) -> ToolResult:
            return ToolResult(outcome="ok")
