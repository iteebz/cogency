"""Tool decorator: function → Tool instance via dataclass schema extraction."""

import inspect
from collections.abc import Callable
from dataclasses import MISSING, fields, is_dataclass
from typing import Annotated, get_args, get_origin

from .protocols import Tool, ToolParam, ToolResult

TYPE_MAP = {str: "string", int: "integer", float: "float", bool: "boolean"}


def _type_name(t) -> str:
    return TYPE_MAP.get(t, "string")


def _base_type(field_type) -> type:
    origin = get_origin(field_type)
    return get_args(field_type)[0] if origin is Annotated else field_type


def _tool_param(field_type) -> ToolParam | None:
    if get_origin(field_type) is not Annotated:
        return None
    args = get_args(field_type)
    matches = [arg for arg in args[1:] if isinstance(arg, ToolParam)]
    return matches[0] if matches else None


def _schema_field(field) -> dict:
    base = _base_type(field.type)
    param = _tool_param(field.type)

    schema = {"type": _type_name(base)}

    if param:
        schema["description"] = param.description
        schema.update(
            {
                "min": param.ge,
                "max": param.le,
                "min_length": param.min_length,
                "max_length": param.max_length,
            }
        )
        schema = {k: v for k, v in schema.items() if v is not None}

    has_default = field.default is not MISSING or field.default_factory is not MISSING
    schema["required"] = not has_default
    if has_default and field.default is not MISSING:
        schema["default"] = field.default

    return schema


def _build_schema(params_type) -> dict:
    return {field.name: _schema_field(field) for field in fields(params_type)}


def tool(desc: str):
    """Decorator: @tool("description") async def name(params: ParamsClass, ...) -> ToolResult.

    Creates a Tool instance from an async function. First parameter must be a dataclass
    with Annotated fields. Additional parameters (sandbox_dir, access, etc.) pass through.
    """

    def decorator(func: Callable) -> Tool:
        sig = inspect.signature(func)
        params_arg = list(sig.parameters.values())[0]
        params_type = params_arg.annotation

        if not is_dataclass(params_type):
            raise TypeError(f"First parameter must be a dataclass, got {params_type}")

        tool_name = func.__name__.lower()
        tool_schema = _build_schema(params_type)
        param_names = {f.name for f in fields(params_type)}

        class FunctionTool(Tool):
            name = tool_name
            description = desc
            schema = tool_schema

            async def execute(self, **kwargs) -> ToolResult:
                tool_params = {k: v for k, v in kwargs.items() if k in param_names}
                other_kwargs = {k: v for k, v in kwargs.items() if k not in param_names}
                params = params_type(**tool_params)
                return await func(params, **other_kwargs)

            def describe(self, args: dict) -> str:
                items = [f"{k}={v}" for k, v in args.items() if v is not None]
                return f"{tool_name}({', '.join(items)})" if items else f"{tool_name}()"

        return FunctionTool()

    return decorator
