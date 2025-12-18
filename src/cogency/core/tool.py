"""@tool decorator: async function → Tool instance."""

import inspect
from collections.abc import Callable
from dataclasses import MISSING, fields, is_dataclass
from typing import Annotated, Any, cast, get_args, get_origin

from .protocols import Tool, ToolParam, ToolResult

TYPE_MAP = {str: "string", int: "integer", float: "float", bool: "boolean"}


def _type_name(t: Any) -> str:
    return TYPE_MAP.get(t, "string")


def _base_type(field_type: Any) -> type:
    origin = get_origin(field_type)
    return get_args(field_type)[0] if origin is Annotated else field_type


def _tool_param(field_type: Any) -> ToolParam | None:
    if get_origin(field_type) is not Annotated:
        return None
    args = get_args(field_type)
    matches = [arg for arg in args[1:] if isinstance(arg, ToolParam)]
    return matches[0] if matches else None


def _schema_field(field: Any) -> dict[str, Any]:
    base = _base_type(field.type)
    param = _tool_param(field.type)

    schema: dict[str, Any] = {"type": _type_name(base)}

    if param:
        schema["description"] = param.description
        if param.ge is not None:
            schema["min"] = param.ge
        if param.le is not None:
            schema["max"] = param.le
        if param.min_length is not None:
            schema["min_length"] = param.min_length
        if param.max_length is not None:
            schema["max_length"] = param.max_length

    has_default = field.default is not MISSING or field.default_factory is not MISSING
    schema["required"] = not has_default
    if has_default and field.default is not MISSING:
        schema["default"] = field.default

    return schema


def _build_schema(params_type: Any) -> dict[str, Any]:
    return {field.name: _schema_field(field) for field in fields(params_type)}


def tool(desc: str):
    def decorator(func: Callable[..., Any]) -> Tool:
        sig = inspect.signature(func)
        params_arg = next(iter(sig.parameters.values()))
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

            async def execute(self, **kwargs: Any) -> ToolResult:
                tool_params: dict[str, Any] = {k: v for k, v in kwargs.items() if k in param_names}
                other_kwargs: dict[str, Any] = {
                    k: v for k, v in kwargs.items() if k not in param_names
                }
                params = cast("Callable[..., Any]", params_type)(**tool_params)
                return await func(params, **other_kwargs)

            def describe(self, args: dict[str, Any]) -> str:
                items = [f"{k}={v}" for k, v in args.items() if v is not None]
                return f"{tool_name}({', '.join(items)})" if items else f"{tool_name}()"

        return FunctionTool()

    return decorator
