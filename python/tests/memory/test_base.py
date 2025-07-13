"""Tests for base memory classes."""
import pytest
from datetime import datetime, UTC
from uuid import uuid4

from cogency.memory.base import MemoryArtifact, BaseMemory


def test_memory_artifact_creation():
    """Test MemoryArtifact creation and defaults."""
    content = "Test content"
    artifact = MemoryArtifact(content=content)
    
    assert artifact.content == content
    assert len(artifact.tags) == 0
    assert len(artifact.metadata) == 0
    assert isinstance(artifact.created_at, datetime)
    assert artifact.created_at.tzinfo == UTC
    assert str(artifact.id)  # UUID should be convertible to string


def test_memory_artifact_with_data():
    """Test MemoryArtifact with custom data."""
    content = "Test content with metadata"
    tags = ["test", "memory"]
    metadata = {"priority": "high", "category": "testing"}
    
    artifact = MemoryArtifact(
        content=content,
        tags=tags,
        metadata=metadata
    )
    
    assert artifact.content == content
    assert artifact.tags == tags
    assert artifact.metadata == metadata


def test_memory_artifact_str_representation():
    """Test MemoryArtifact string representation."""
    # Short content
    short_content = "Short content"
    artifact = MemoryArtifact(content=short_content, tags=["test"])
    str_repr = str(artifact)
    
    assert "MemoryArtifact" in str_repr
    assert short_content in str_repr
    assert "['test']" in str_repr
    
    # Long content (should be truncated)
    long_content = "A" * 100
    artifact_long = MemoryArtifact(content=long_content)
    str_repr_long = str(artifact_long)
    
    assert "MemoryArtifact" in str_repr_long
    assert "..." in str_repr_long
    assert len(str_repr_long) < len(long_content) + 50  # Should be truncated


def test_base_memory_interface():
    """Test that BaseMemory is properly abstract."""
    with pytest.raises(TypeError):
        BaseMemory()  # Should not be instantiable