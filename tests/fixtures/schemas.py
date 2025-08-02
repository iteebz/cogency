"""Schema validation fixtures for testing."""

import pytest


@pytest.fixture
def validation_schemas():
    """Pre-validated response schemas for testing."""
    return {
        "tool_call": {
            "type": "object",
            "properties": {
                "tool_name": {"type": "string"},
                "parameters": {"type": "object"},
                "result": {"oneOf": [{"type": "string"}, {"type": "object"}]},
            },
            "required": ["tool_name", "parameters"],
        },
        "llm_response": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "minLength": 1},
                "tokens": {"type": "integer", "minimum": 0},
                "model": {"type": "string"},
            },
            "required": ["content"],
        },
        "memory_entry": {
            "type": "object",
            "properties": {
                "content": {"type": "string"},
                "timestamp": {"type": "string", "format": "date-time"},
                "user_id": {"type": "string"},
                "human": {"type": "boolean"},
            },
            "required": ["content", "human"],
        },
    }
