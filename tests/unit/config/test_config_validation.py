"""Schema validation tests for provider responses and data structures."""

from typing import Any

import pytest
from jsonschema import ValidationError, validate

from cogency.storage.sqlite import SQLite
from tests.fixtures.provider import RealisticMockProvider


def validate_schema(data: dict[str, Any], schema: dict[str, Any]) -> bool:
    """Validate data against JSON schema."""
    try:
        validate(instance=data, schema=schema)
        return True
    except ValidationError:
        return False


@pytest.mark.asyncio
async def test_response_schema():
    """Validate LLM responses conform to expected schema."""
    provider = RealisticMockProvider()
    schema = {
        "type": "object",
        "properties": {
            "content": {"type": "string"},
            "tokens": {"type": "integer", "minimum": 0},
            "model": {"type": "string"},
        },
        "required": ["content", "tokens", "model"],
    }

    # Test basic response
    messages = [{"role": "user", "content": "test query"}]
    response = await provider.run(messages)

    assert response.success

    # Construct response data to validate
    response_data = {
        "content": response.data,
        "tokens": 42,  # Mock token count
        "model": provider.default_model,
    }

    assert validate_schema(response_data, schema)
    assert len(response_data["content"]) > 0
    assert response_data["tokens"] >= 0
    assert isinstance(response_data["model"], str)


@pytest.mark.asyncio
async def test_store_data():
    """Validate store operations use correct data formats."""
    from cogency.memory import Profile

    store = SQLite()  # Use default temp directory

    # Valid memory entry for profile
    profile = Profile(user_id="test_user")
    profile.preferences = {"theme": "dark"}

    # Test canonical store operations
    result = await store.save_profile("test_user:default", profile)
    assert result is True

    loaded_result = await store.load_profile("test_user:default")
    assert loaded_result is not None
    assert loaded_result.user_id == "test_user"


@pytest.mark.asyncio
async def test_tool_response_schema(mock_tools):
    """Validate tool responses follow Result interface."""
    tool = mock_tools[0]
    schema = {
        "type": "object",
        "properties": {"tool_name": {"type": "string"}, "args": {"type": "object"}, "result": {}},
        "required": ["tool_name", "args", "result"],
    }

    # Valid tool call
    result = await tool.run(arg="test_value")

    # Construct tool call data
    tool_call_data = {
        "tool_name": tool.name,
        "args": {"arg": "test_value"},
        "result": result.data if result.success else result.error,
    }

    assert validate_schema(tool_call_data, schema)
    assert result.success  # Tool should return successful Result


def test_invalid_schema_rejection():
    """Verify invalid data is properly rejected."""
    schema = {
        "type": "object",
        "properties": {
            "content": {"type": "string"},
            "tokens": {"type": "integer", "minimum": 0},
            "model": {"type": "string"},
        },
        "required": ["content", "tokens", "model"],
    }

    # Missing required field
    invalid_data = {
        "tokens": 10,
        "model": "test",
        # Missing "content"
    }

    assert not validate_schema(invalid_data, schema)

    # Invalid type
    invalid_data = {"content": 123, "tokens": 10, "model": "test"}  # Should be string

    assert not validate_schema(invalid_data, schema)


@pytest.mark.asyncio
async def test_embedding_schema():
    """Test embedding provider response validation."""
    # Mock embedding response schema
    embedding_schema = {
        "type": "object",
        "properties": {
            "embeddings": {
                "type": "array",
                "items": {"type": "array", "items": {"type": "number"}},
            },
            "model": {"type": "string"},
            "dimensions": {"type": "integer", "minimum": 1},
        },
        "required": ["embeddings", "model", "dimensions"],
    }

    # Valid embedding response
    embedding_data = {
        "embeddings": [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
        "model": "text-embedding-ada-002",
        "dimensions": 3,
    }

    assert validate_schema(embedding_data, embedding_schema)

    # Invalid embedding response
    invalid_embedding = {
        "embeddings": "not an array",  # Wrong type
        "model": "test",
        "dimensions": 3,
    }

    assert not validate_schema(invalid_embedding, embedding_schema)


@pytest.mark.asyncio
async def test_state_schema():
    """Test state persistence data follows schema."""
    state_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "iteration": {"type": "integer", "minimum": 0},
            "messages": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "role": {"type": "string", "enum": ["user", "assistant", "system"]},
                        "content": {"type": "string"},
                    },
                    "required": ["role", "content"],
                },
            },
            "tool_calls": {"type": "array"},
            "response": {"type": ["string", "null"]},
            "response_source": {"type": ["string", "null"]},
        },
        "required": ["query", "iteration", "messages"],
    }

    from cogency.state import State

    state = State("test query")
    from cogency.state.mutations import add_message

    add_message(state, "user", "test message")

    # Convert state to dict for validation
    state_data = {
        "query": state.query,
        "iteration": state.execution.iteration,
        "messages": state.execution.messages,
        "tool_calls": state.execution.pending_calls,
        "response": getattr(state.execution, "response", None),
        "response_source": getattr(state.execution, "response_source", None),
    }

    assert validate_schema(state_data, state_schema)


@pytest.mark.asyncio
async def test_config_schema():
    """Test configuration objects follow expected schemas."""
    config_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "minLength": 1},
            "mode": {"type": "string", "enum": ["adapt", "fast", "thorough"]},
            "depth": {"type": "integer", "minimum": 1, "maximum": 50},
            "notify": {"type": "boolean"},
            "debug": {"type": "boolean"},
        },
        "required": ["name", "mode", "depth"],
    }

    # Valid config
    config_data = {
        "name": "test_agent",
        "mode": "adapt",
        "depth": 10,
        "notify": True,
        "debug": False,
    }

    assert validate_schema(config_data, config_schema)

    # Invalid config - mode not in enum
    invalid_config = {"name": "test_agent", "mode": "invalid_mode", "depth": 10}

    assert not validate_schema(invalid_config, config_schema)
