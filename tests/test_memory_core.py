"""Test memory types and artifacts."""
import pytest
import time
from datetime import datetime, UTC

from cogency.memory.core import Memory, MemoryType


class TestMemoryCore:
    """Test memory types and artifacts."""
    
    def test_memory_creation(self):
        memory = Memory(
            content="test memory",
            memory_type=MemoryType.FACT,
            tags=["test"]
        )
        
        assert memory.content == "test memory"
        assert memory.memory_type == MemoryType.FACT
        assert "test" in memory.tags
        assert memory.id is not None
        assert isinstance(memory.created_at, datetime)
    
    def test_decay_score_calculation(self):
        memory = Memory(content="test", confidence_score=1.0)
        
        # Fresh memory should have high decay score
        score = memory.decay()
        assert 0.8 < score <= 1.0  # Should be close to confidence_score
    
    def test_memory_access_tracking(self):
        memory = Memory(content="test")
        
        initial_count = memory.access_count
        initial_accessed = memory.last_accessed
        
        # Simulate access (would be done by backend)
        time.sleep(0.001)  # Ensure timestamp difference
        memory.access_count += 1
        memory.last_accessed = datetime.now(UTC)
        
        assert memory.access_count == initial_count + 1
        assert memory.last_accessed > initial_accessed
    
    def test_memory_type_enum(self):
        """Test memory type enumeration."""
        assert MemoryType.FACT
        assert MemoryType.PREFERENCE
        assert MemoryType.EXPERIENCE
        
        # Should be able to create memories with different types
        fact = Memory(content="fact", memory_type=MemoryType.FACT)
        preference = Memory(content="preference", memory_type=MemoryType.PREFERENCE)
        experience = Memory(content="experience", memory_type=MemoryType.EXPERIENCE)
        
        assert fact.memory_type == MemoryType.FACT
        assert preference.memory_type == MemoryType.PREFERENCE
        assert experience.memory_type == MemoryType.EXPERIENCE