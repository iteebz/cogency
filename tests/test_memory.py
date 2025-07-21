"""Test memory system: backends, search, smart heuristics."""
import pytest
from uuid import uuid4

from cogency.memory.core import MemoryType, SearchType
from cogency.memory.backends.filesystem import FileBackend


class TestMemoryBackends:
    """Test memory backend contracts and behavior."""
    
    @pytest.mark.asyncio
    async def test_basic_memorize_recall_flow(self, memory_backend):
        """Basic store and retrieve should work."""
        # Store a memory
        artifact = await memory_backend.create(
            "I work as a software engineer at Google",
            memory_type=MemoryType.FACT,
            tags=["work", "personal"]
        )
        
        assert artifact.content == "I work as a software engineer at Google"
        assert artifact.memory_type == MemoryType.FACT
        assert "work" in artifact.tags
        
        # Retrieve it
        results = await memory_backend.read(query="software engineer")
        
        assert len(results) >= 1
        found = any("software engineer" in r.content for r in results)
        assert found
    
    @pytest.mark.asyncio
    async def test_memory_filtering(self, memory_backend, sample_memory_content):
        """Memory recall should support filtering."""
        # Store sample memories
        for item in sample_memory_content:
            await memory_backend.create(
                item["content"],
                tags=item["tags"]
            )
        
        # Filter by tags
        personal_memories = await memory_backend.read(query=
            "",
            search_type=SearchType.TAGS,
            tags=["personal"]
        )
        
        assert len(personal_memories) >= 2  # ADHD+engineer and location
        for memory in personal_memories:
            assert "personal" in memory.tags
    
    @pytest.mark.asyncio
    async def test_user_isolation(self, temp_memory_dir):
        """Different users should have isolated memory."""
        backend1 = FileBackend(memory_dir=temp_memory_dir)
        backend2 = FileBackend(memory_dir=temp_memory_dir)
        
        # Store memory for user1
        await backend1.create("user1 secret", user_id="user1")
        
        # User2 shouldn't see user1's memory
        results = await backend2.read(query="secret", user_id="user2")
        assert len(results) == 0
        
        # User1 should still see their own memory
        results = await backend1.read(query="secret", user_id="user1")
        assert len(results) >= 1
    
    @pytest.mark.asyncio
    async def test_memory_persistence(self, temp_memory_dir):
        """Memory should persist across backend instances."""
        # Store memory with first backend instance
        backend1 = FileBackend(memory_dir=temp_memory_dir)
        artifact = await backend1.create("persistent memory test")
        
        # Create new backend instance (simulates restart)
        backend2 = FileBackend(memory_dir=temp_memory_dir)
        results = await backend2.read(query="persistent memory")
        
        assert len(results) >= 1
        assert any("persistent memory test" in r.content for r in results)
    
    @pytest.mark.asyncio
    async def test_forget_functionality(self, memory_backend):
        """Should be able to delete specific memories."""
        # Store a memory
        artifact = await memory_backend.create("temporary memory")
        memory_id = artifact.id
        
        # Verify it exists
        results = await memory_backend.read(query="temporary")
        assert len(results) >= 1
        
        # Delete it
        success = await memory_backend.delete(artifact_id=memory_id)
        assert success
        
        # Verify it's gone
        results = await memory_backend.read(query="temporary")
        assert len(results) == 0


class TestMemorySearch:
    """Test memory search algorithms and ranking."""
    
    @pytest.mark.asyncio
    async def test_semantic_search_ranking(self, memory_backend):
        """More relevant memories should rank higher."""
        # Store memories with different relevance levels
        await memory_backend.create("I love programming in Python")
        await memory_backend.create("I had lunch today")
        await memory_backend.create("Python is my favorite programming language")
        
        # Search for programming-related content
        results = await memory_backend.read(query="python programming")
        
        assert len(results) >= 2
        # More specific match should rank higher
        assert "Python is my favorite" in results[0].content
    
    @pytest.mark.asyncio
    async def test_search_type_behavior(self, memory_backend):
        """Different search types should work."""
        await memory_backend.create("I work with Python daily", tags=["tech"])
        
        # Text search should find exact matches
        results = await memory_backend.read(query=
            "Python",
            search_type=SearchType.TEXT
        )
        assert len(results) >= 1
        
        # Tag search should work
        results = await memory_backend.read(query=
            "",
            search_type=SearchType.TAGS,
            tags=["tech"]
        )
        assert len(results) >= 1


class TestMemoryIntelligence:
    """Test CRUD operations."""
    
    @pytest.mark.asyncio
    async def test_crud_operations(self, memory_backend):
        """Test full CRUD cycle."""
        # CREATE
        artifact = await memory_backend.create("Test content", tags=["test"])
        assert artifact.content == "Test content"
        
        # READ by ID
        results = await memory_backend.read(artifact_id=artifact.id)
        assert len(results) == 1
        assert results[0].content == "Test content"
        
        # UPDATE
        success = await memory_backend.update(artifact.id, {"tags": ["updated"]})
        assert success is True
        
        # Verify update
        results = await memory_backend.read(artifact_id=artifact.id)
        assert "updated" in results[0].tags
        
        # DELETE
        success = await memory_backend.delete(artifact_id=artifact.id)
        assert success is True
        
        # Verify deletion
        results = await memory_backend.read(artifact_id=artifact.id)
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_flexible_delete(self, memory_backend):
        """Test delete by filters."""
        # Create multiple artifacts
        await memory_backend.create("Test 1", tags=["temp"])
        await memory_backend.create("Test 2", tags=["temp"])
        await memory_backend.create("Test 3", tags=["keep"])
        
        # Delete by tag
        success = await memory_backend.delete(tags=["temp"])
        assert success is True
        
        # Verify only non-temp artifacts remain
        results = await memory_backend.read()
        assert len(results) == 1
        assert "Test 3" in results[0].content


class TestMemoryAutoConfiguration:
    """Test Memory.create() auto-magical backend creation."""
    
    def test_file_backend_creation(self, temp_memory_dir):
        """Should auto-create filesystem backend."""
        from cogency.memory.core import Memory
        
        backend = Memory.create("filesystem", memory_dir=temp_memory_dir)
        
        assert isinstance(backend, FileBackend)
        assert backend.memory_dir.name == temp_memory_dir.split("/")[-1]
    
    def test_list_available_backends(self):
        """Should list available backend types."""
        from cogency.memory.core import Memory
        
        backends = Memory.list_backends()
        
        assert isinstance(backends, list)
        assert "filesystem" in backends
        assert len(backends) >= 1