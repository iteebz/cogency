"""Tool validation business logic tests."""

from dataclasses import dataclass

import pytest

from cogency.tools.validation import validate


@dataclass
class TestSchema:
    name: str
    age: int
    active: bool = True


@dataclass
class ComplexSchema:
    required_field: str
    optional_field: str = "default"
    number_field: int = 0


def test_validate_success():
    """Test successful validation with valid arguments."""
    args = {"name": "John", "age": 30, "active": False}

    result = validate(args, TestSchema)

    assert isinstance(result, TestSchema)
    assert result.name == "John"
    assert result.age == 30
    assert result.active is False


def test_validate_with_defaults():
    """Test validation uses schema defaults for missing fields."""
    args = {"name": "Jane", "age": 25}

    result = validate(args, TestSchema)

    assert result.name == "Jane"
    assert result.age == 25
    assert result.active is True  # Default value


def test_validate_missing_required_field():
    """Test validation fails for missing required fields."""
    args = {"name": "John"}  # Missing required 'age'

    with pytest.raises(ValueError, match="Argument validation failed"):
        validate(args, TestSchema)


def test_validate_extra_arguments():
    """Test validation ignores extra arguments."""
    args = {"name": "John", "age": 30, "extra_field": "ignored"}

    result = validate(args, TestSchema)

    assert result.name == "John"
    assert result.age == 30
    assert not hasattr(result, "extra_field")


def test_validate_wrong_type():
    """Test validation accepts arguments (Python dataclasses don't validate types by default)."""
    args = {"name": "John", "age": "thirty"}  # String instead of int

    # Python dataclasses don't validate types by default, so this should succeed
    result = validate(args, TestSchema)
    assert result.name == "John"
    assert result.age == "thirty"  # Type annotation is ignored by Python


def test_validate_non_dataclass_schema():
    """Test validation raises error for non-dataclass schemas."""

    class NotADataclass:
        pass

    args = {"field": "value"}

    with pytest.raises(ValueError, match="is not a dataclass"):
        validate(args, NotADataclass)


def test_validate_empty_args():
    """Test validation handles empty arguments with required fields."""
    args = {}

    with pytest.raises(ValueError, match="Argument validation failed"):
        validate(args, TestSchema)


def test_validate_complex_schema():
    """Test validation with complex schema having mixed defaults."""
    args = {"required_field": "test"}

    result = validate(args, ComplexSchema)

    assert result.required_field == "test"
    assert result.optional_field == "default"
    assert result.number_field == 0


def test_validate_override_all_defaults():
    """Test validation allows overriding all default values."""
    args = {"required_field": "test", "optional_field": "custom", "number_field": 42}

    result = validate(args, ComplexSchema)

    assert result.required_field == "test"
    assert result.optional_field == "custom"
    assert result.number_field == 42


def test_validate_preserves_original_args():
    """Test validation does not modify original arguments dictionary."""
    args = {"name": "John", "age": 30}
    original_args = args.copy()

    validate(args, TestSchema)

    assert args == original_args  # Original dict unchanged
