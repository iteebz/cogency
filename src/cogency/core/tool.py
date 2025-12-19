"""@tool decorator: async function → Tool instance."""

import inspect
from collections.abc import Callable
from dataclasses import MISSING, fields, is_dataclass
from typing import Annotated, Any, cast, get_args, get_origin

from .errors import ToolError
from .protocols import Tool, ToolParam, ToolResult

TYPE_MAP = {str: "string", int: "integer", float: "float", bool: "boolean"}


def _type_name(t: Any) -> str:
    origin = get_origin(t)
    if origin is Annotated:
        t = get_args(t)[0]
        origin = get_origin(t)
    # Handle Union types (X | None) - use first non-None type
    import types

    if origin in (type(None) | type, types.UnionType):
        args = [a for a in get_args(t) if a is not type(None)]
        if args:
            t = args[0]
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


def _check_type(name: str, value: Any, field_type: str) -> str | None:
    """Check type, return error message or None."""
    checks: dict[str, type | tuple[type, ...]] = {
        "string": str,
        "integer": int,
        "float": (int, float),
        "boolean": bool,
    }
    if field_type in checks and not isinstance(value, checks[field_type]):
        return f"{name}: expected {field_type}, got {type(value).__name__}"
    return None


def _check_bounds(name: str, value: Any, spec: dict[str, Any]) -> list[str]:
    """Check numeric bounds and string length."""
    errors: list[str] = []
    if isinstance(value, (int, float)):
        if "min" in spec and value < spec["min"]:
            errors.append(f"{name}: value {value} < min {spec['min']}")
        if "max" in spec and value > spec["max"]:
            errors.append(f"{name}: value {value} > max {spec['max']}")
    if isinstance(value, str):
        if "min_length" in spec and len(value) < spec["min_length"]:
            errors.append(f"{name}: length {len(value)} < min_length {spec['min_length']}")
        if "max_length" in spec and len(value) > spec["max_length"]:
            errors.append(f"{name}: length {len(value)} > max_length {spec['max_length']}")
    return errors


def _validate_args(schema: dict[str, Any], args: dict[str, Any]) -> None:
    """Validate args against schema. Raises ToolError on failure."""
    errors: list[str] = []

    for name, spec in schema.items():
        value = args.get(name)
        if value is None:
            if spec.get("required", False):
                errors.append(f"Missing required field: {name}")
            continue

        type_err = _check_type(name, value, spec.get("type", "string"))
        if type_err:
            errors.append(type_err)
        errors.extend(_check_bounds(name, value, spec))

    if errors:
        raise ToolError("; ".join(errors), validation_failed=True)


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
                _validate_args(tool_schema, tool_params)
                params = cast("Callable[..., Any]", params_type)(**tool_params)
                return await func(params, **other_kwargs)

            def describe(self, args: dict[str, Any]) -> str:
                items = [f"{k}={v}" for k, v in args.items() if v is not None]
                return f"{tool_name}({', '.join(items)})" if items else f"{tool_name}()"

        return FunctionTool()

    return decorator
