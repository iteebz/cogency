"""Shared utilities for robust LLM response handling."""

from .cli import interactive_mode, main, trace_args
from .detection import detect_provider
from .formatting import format_tool_error, format_tool_params, summarize_result, truncate
from .heuristics import is_simple_query
from .keys import KeyManager, KeyRotator
from .parsing import normalize_reasoning, parse_json, parse_json_with_correction, parse_tool_calls
from .providers import Provider
from .validation import validate_query

__all__ = [
    "format_tool_params",
    "interactive_mode",
    "main",
    "parse_json",
    "summarize_result",
    "trace_args",
    "validate_query",
    "is_simple_query",
    "parse_json_with_correction",
    "parse_tool_calls",
    "normalize_reasoning",
    "KeyManager",
    "KeyRotator",
    "truncate",
    "format_tool_error",
    "Provider",
    "detect_provider",
]
