"""Universal signature-based parsing: Natural function syntax with Python introspection."""

import ast
import inspect
import re
from typing import Any

from .result import Err, Ok, Result


def parse_tool_call(call_str: str) -> Result[dict[str, Any], str]:
    """Parse tool call syntax: USE: retrieve("query, with commas", limit=5)

    Returns:
        Ok({"tool": "retrieve", "args": {"arg_0": "...", "limit": 5}}) on success
        Err("Parse error: ...") on failure
    """
    try:
        # Extract tool call from USE: prefix
        match = re.search(r"USE:\s*(\w+)\((.*?)\)$", call_str.strip(), re.IGNORECASE)
        if not match:
            return Err("No tool call found")

        tool_name = match.group(1)
        args_str = match.group(2).strip()

        # Handle empty args
        if not args_str:
            return Ok({"tool": tool_name, "args": {}})

        # Use AST to parse natural function arguments
        try:
            parsed = ast.parse(f"func({args_str})").body[0].value
        except SyntaxError as e:
            return Err(f"Invalid syntax: {str(e)}")

        args = {}

        # Handle positional arguments
        if hasattr(parsed, "args") and parsed.args:
            for i, arg in enumerate(parsed.args):
                args[f"arg_{i}"] = ast.literal_eval(arg)

        # Handle keyword arguments
        if hasattr(parsed, "keywords") and parsed.keywords:
            for keyword in parsed.keywords:
                args[keyword.arg] = ast.literal_eval(keyword.value)

        return Ok({"tool": tool_name, "args": args})

    except Exception as e:
        return Err(f"Parse error: {str(e)}")


def parse_with_signature(call_str: str, tool_instance) -> Result[dict[str, Any], str]:
    """Parse tool call using actual tool signature for parameter mapping.

    Args:
        call_str: Tool call string like 'USE: retrieve("query", limit=5)'
        tool_instance: Tool instance with execute method

    Returns:
        Ok({"tool": "name", "args": {"query": "...", "limit": 5}}) on success
        Err("Parse error: ...") on failure
    """
    try:
        # Extract tool call from USE: prefix
        match = re.search(r"USE:\s*(\w+)\((.*?)\)$", call_str.strip(), re.IGNORECASE)
        if not match:
            return Err("No tool call found")

        tool_name = match.group(1)
        args_str = match.group(2).strip()

        # Handle empty args
        if not args_str:
            return Ok({"tool": tool_name, "args": {}})

        # Get tool's execute method signature
        try:
            sig = inspect.signature(tool_instance.execute)
            params = list(sig.parameters.values())
            # Filter out 'self' parameter
            params = [p for p in params if p.name != "self"]
        except Exception as e:
            return Err(f"Failed to get tool signature: {str(e)}")

        # Use AST to parse natural function arguments
        try:
            parsed = ast.parse(f"func({args_str})").body[0].value
        except SyntaxError as e:
            return Err(f"Invalid syntax: {str(e)}")

        args = {}

        # Map positional arguments to parameter names
        if hasattr(parsed, "args") and parsed.args:
            for i, arg_value in enumerate(parsed.args):
                if i < len(params):
                    param_name = params[i].name
                    args[param_name] = ast.literal_eval(arg_value)
                else:
                    # Extra positional args get generic names
                    args[f"arg_{i}"] = ast.literal_eval(arg_value)

        # Handle keyword arguments (override positional mappings)
        if hasattr(parsed, "keywords") and parsed.keywords:
            for keyword in parsed.keywords:
                args[keyword.arg] = ast.literal_eval(keyword.value)

        # Apply parameter defaults for missing args
        for param in params:
            if param.name not in args and param.default != inspect.Parameter.empty:
                args[param.name] = param.default

        return Ok({"tool": tool_name, "args": args})

    except Exception as e:
        return Err(f"Parse error: {str(e)}")
