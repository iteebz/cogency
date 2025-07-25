"""Lightweight schema parsing and validation using dataclasses."""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ParamSpec:
    """Parameter specification parsed from schema."""

    name: str
    type_hint: str
    required: bool = True
    default: Any = None


@dataclass
class SchemaSpec:
    """Complete schema specification."""

    tool_name: str
    params: List[ParamSpec] = field(default_factory=list)


def parse_tool_schema(schema_str: str) -> Optional[SchemaSpec]:
    """Parse tool schema string into structured validation spec.

    Example schema: "search(query='string', max_results=5)\nRequired: query | Optional: max_results"
    Returns: SchemaSpec with ParamSpec objects for validation
    """
    if not schema_str or not schema_str.strip():
        return None

    # Split schema and requirements
    lines = schema_str.strip().split("\n")
    schema_line = lines[0]

    # Extract tool name and parameters
    match = re.match(r"^(\w+)\s*\((.*)\)", schema_line.strip())
    if not match:
        return None

    tool_name = match.group(1)
    params_str = match.group(2)

    params = []
    if params_str.strip():
        # Split parameters, handling nested structures
        param_parts = _split_params(params_str)

        for part in param_parts:
            param_spec = _parse_param(part.strip())
            if param_spec:
                params.append(param_spec)

    # Parse Required/Optional notation if present
    if len(lines) > 1:
        _apply_requirements(params, lines[1:])

    return SchemaSpec(tool_name=tool_name, params=params)


def _apply_requirements(params: List[ParamSpec], requirement_lines: List[str]) -> None:
    """Apply Required/Optional requirements from schema lines."""
    required_params = set()
    optional_params = set()

    for line in requirement_lines:
        line = line.strip()
        if line.startswith("Required:"):
            # Extract parameter names after "Required:"
            req_part = line[9:].strip()  # Remove "Required:"
            if "|" in req_part:
                req_part = req_part.split("|")[0].strip()
            required_params.update(p.strip() for p in req_part.split(",") if p.strip())
        elif line.startswith("Optional:"):
            # Extract parameter names after "Optional:"
            opt_part = line[9:].strip()  # Remove "Optional:"
            if "|" in opt_part:
                opt_part = opt_part.split("|")[0].strip()
            optional_params.update(p.strip() for p in opt_part.split(",") if p.strip())

    # Apply requirements to params
    for param in params:
        if param.name in required_params:
            param.required = True
        elif param.name in optional_params:
            param.required = False


def _split_params(params_str: str) -> List[str]:
    """Split parameter string, respecting nested brackets/quotes."""
    parts = []
    current = ""
    depth = 0
    in_quote = False
    quote_char = None

    for char in params_str:
        if char in ('"', "'") and not in_quote:
            in_quote = True
            quote_char = char
        elif char == quote_char and in_quote:
            in_quote = False
            quote_char = None
        elif not in_quote:
            if char in ("(", "[", "{"):
                depth += 1
            elif char in (")", "]", "}"):
                depth -= 1
            elif char == "," and depth == 0:
                if current.strip():
                    parts.append(current.strip())
                current = ""
                continue

        current += char

    if current.strip():
        parts.append(current.strip())

    return parts


def _parse_param(param_str: str) -> Optional[ParamSpec]:
    """Parse single parameter specification."""
    # Handle: name='type' or name=default_value
    if "=" not in param_str:
        return ParamSpec(name=param_str, type_hint="any", required=True)

    name, value_part = param_str.split("=", 1)
    name = name.strip()
    value_part = value_part.strip()

    # Extract type hint from quoted values or infer from default
    if value_part.startswith("'") and value_part.endswith("'"):
        type_hint = value_part[1:-1]  # Extract quoted type
        # If it's just a type hint (no actual default), it's optional
        return ParamSpec(name=name, type_hint=type_hint, required=False)
    else:
        # Infer type from default value
        default_val = _parse_default_value(value_part)
        type_hint = type(default_val).__name__ if default_val is not None else "any"
        return ParamSpec(name=name, type_hint=type_hint, required=False, default=default_val)


def _parse_default_value(value_str: str) -> Any:
    """Parse default value from string."""
    value_str = value_str.strip()

    # Boolean
    if value_str.lower() in ("true", "false"):
        return value_str.lower() == "true"

    # None/null
    if value_str.lower() in ("none", "null"):
        return None

    # Integer
    try:
        return int(value_str)
    except ValueError:
        pass

    # Float
    try:
        return float(value_str)
    except ValueError:
        pass

    # String (unquoted)
    return value_str


def validate_params(params: Dict[str, Any], schema_spec: SchemaSpec) -> Dict[str, Any]:
    """Validate parameters against schema specification."""
    validated = {}

    # Check required parameters
    for param_spec in schema_spec.params:
        if param_spec.required and param_spec.name not in params:
            raise ValueError(f"Missing required parameter: {param_spec.name}")

        if param_spec.name in params:
            value = params[param_spec.name]
            validated[param_spec.name] = _coerce_type(value, param_spec.type_hint, param_spec.name)
        elif param_spec.default is not None:
            validated[param_spec.name] = param_spec.default

    # Include any additional parameters (tools may accept **kwargs)
    for key, value in params.items():
        if key not in validated:
            validated[key] = value

    return validated


def _coerce_type(value: Any, type_hint: str, param_name: str) -> Any:
    """Coerce value to expected type with validation."""
    if type_hint == "any":
        return value

    # String validation
    if type_hint == "string":
        if value is None:
            raise ValueError(f"Parameter {param_name} cannot be None")
        return str(value)

    # Integer validation
    if type_hint in ("int", "integer"):
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
        raise ValueError(f"Parameter {param_name} must be an integer, got {type(value).__name__}")

    # Float validation
    if type_hint == "float":
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                pass
        raise ValueError(f"Parameter {param_name} must be a number, got {type(value).__name__}")

    # Boolean validation
    if type_hint in ("bool", "boolean"):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            if value.lower() in ("true", "1", "yes"):
                return True
            if value.lower() in ("false", "0", "no"):
                return False
        raise ValueError(f"Parameter {param_name} must be a boolean, got {type(value).__name__}")

    # Dict validation
    if type_hint in ("dict", "object"):
        if not isinstance(value, dict):
            raise ValueError(
                f"Parameter {param_name} must be a dictionary, got {type(value).__name__}"
            )
        return value

    # List validation
    if type_hint in ("list", "array"):
        if not isinstance(value, list):
            raise ValueError(f"Parameter {param_name} must be a list, got {type(value).__name__}")
        return value

    # Default: return as-is for unknown types
    return value
