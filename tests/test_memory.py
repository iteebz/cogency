"""Test memory system: backends, search, smart heuristics."""
import pytest
from uuid import uuid4

from cogency.memory.core import MemoryType, SearchType
from cogency.memory.backends.filesystem import FilesystemBackend


class TestMemoryBackends:
    """Test memory backend contracts and behavior."""
    
    @pytest.mark.asyncio
    async def test_basic_memorize_recall_flow(self, memory_backend):
        """Basic store and retrieve should work."""
        # Store a memory
        artifact = await memory_backend.memorize(
            "I work as a software engineer at Google",
            memory_type=MemoryType.FACT,
            tags=["work", "personal"]
        )
        
        assert artifact.content == "I work as a software engineer at Google"
        assert artifact.memory_type == MemoryType.FACT
        assert "work" in artifact.tags
        
        # Retrieve it
        results = await memory_backend.recall("software engineer")
        
        assert len(results) >= 1
        found = any("software engineer" in r.content for r in results)
        assert found
    
    @pytest.mark.asyncio
    async def test_memory_filtering(self, memory_backend, sample_memory_content):
        """Memory recall should support filtering."""
        # Store sample memories
        for item in sample_memory_content:
            await memory_backend.memorize(
                item["content"],
                tags=item["tags"]
            )
        
        # Filter by tags
        personal_memories = await memory_backend.recall(
            "anything",
            tags=["personal"]
        )
        
        assert len(personal_memories) >= 2  # ADHD+engineer and location
        for memory in personal_memories:
            assert "personal" in memory.tags
    
    @pytest.mark.asyncio
    async def test_user_isolation(self, temp_memory_dir):
        """Different users should have isolated memory."""
        backend1 = FilesystemBackend(memory_dir=temp_memory_dir)
        backend2 = FilesystemBackend(memory_dir=temp_memory_dir)
        
        # Store memory for user1
        await backend1.memorize("user1 secret", user_id="user1")
        
        # User2 shouldn't see user1's memory
        results = await backend2.recall("secret", user_id="user2")
        assert len(results) == 0
        
        # User1 should still see their own memory
        results = await backend1.recall("secret", user_id="user1")
        assert len(results) >= 1
    
    @pytest.mark.asyncio
    async def test_memory_persistence(self, temp_memory_dir):
        """Memory should persist across backend instances."""
        # Store memory with first backend instance
        backend1 = FilesystemBackend(memory_dir=temp_memory_dir)
        artifact = await backend1.memorize("persistent memory test")
        
        # Create new backend instance (simulates restart)
        backend2 = FilesystemBackend(memory_dir=temp_memory_dir)
        results = await backend2.recall("persistent memory")
        
        assert len(results) >= 1
        assert any("persistent memory test" in r.content for r in results)
    
    @pytest.mark.asyncio
    async def test_forget_functionality(self, memory_backend):
        """Should be able to delete specific memories."""
        # Store a memory
        artifact = await memory_backend.memorize("temporary memory")
        memory_id = artifact.id
        
        # Verify it exists
        results = await memory_backend.recall("temporary")
        assert len(results) >= 1
        
        # Delete it
        success = await memory_backend.forget(memory_id)
        assert success
        
        # Verify it's gone
        results = await memory_backend.recall("temporary")
        assert len(results) == 0


class TestMemorySearch:
    """Test memory search algorithms and ranking."""
    
    @pytest.mark.asyncio
    async def test_semantic_search_ranking(self, memory_backend):
        """More relevant memories should rank higher."""
        # Store memories with different relevance levels
        await memory_backend.memorize("I love programming in Python")
        await memory_backend.memorize("I had lunch today")
        await memory_backend.memorize("Python is my favorite programming language")
        
        # Search for programming-related content
        results = await memory_backend.recall("python programming")
        
        assert len(results) >= 2
        # More specific match should rank higher
        assert "Python is my favorite" in results[0].content
    
    @pytest.mark.asyncio
    async def test_search_type_behavior(self, memory_backend):
        """Different search types should work."""
        await memory_backend.memorize("I work with Python daily", tags=["tech"])
        
        # Text search should find exact matches
        results = await memory_backend.recall(
            "Python",
            search_type=SearchType.TEXT
        )
        assert len(results) >= 1
        
        # Tag search should work
        results = await memory_backend.recall(
            "",
            search_type=SearchType.TAGS,
            tags=["tech"]
        )
        assert len(results) >= 1


class TestMemoryHeuristics:
    """Test smart memory storage heuristics."""
    
    def test_should_store_personal_info(self, memory_backend):
        """Should detect personal information worth storing."""
        # Personal triggers
        assert memory_backend.should_store("I have ADHD") == (True, "personal")
        assert memory_backend.should_store("My name is John") == (True, "personal")
        assert memory_backend.should_store("I am 25 years old") == (True, "personal")
    
    def test_should_store_work_info(self, memory_backend):
        """Should detect work-related information."""
        assert memory_backend.should_store("I work at Google") == (True, "work")
        assert memory_backend.should_store("I'm a software engineer") == (True, "work")
        assert memory_backend.should_store("My job involves data analysis") == (True, "work")
    
    def test_should_store_preferences(self, memory_backend):
        """Should detect preferences worth remembering."""
        assert memory_backend.should_store("I like quiet environments") == (True, "preferences")
        assert memory_backend.should_store("I prefer coffee over tea") == (True, "preferences")
    
    def test_should_not_store_trivial(self, memory_backend):
        """Should not store trivial conversational content."""
        assert memory_backend.should_store("Hello there") == (False, "")
        assert memory_backend.should_store("What's the weather?") == (False, "")
        assert memory_backend.should_store("Thanks") == (False, "")


class TestMemoryAutoConfiguration:
    """Test Memory.create() auto-magical backend creation."""
    
    def test_filesystem_backend_creation(self, temp_memory_dir):
        """Should auto-create filesystem backend."""
        from cogency.memory.core import Memory
        
        backend = Memory.create("filesystem", memory_dir=temp_memory_dir)
        
        assert isinstance(backend, FilesystemBackend)
        assert backend.memory_dir.name == temp_memory_dir.split("/")[-1]
    
    def test_list_available_backends(self):
        """Should list available backend types."""
        from cogency.memory.core import Memory
        
        backends = Memory.list_backends()
        
        assert isinstance(backends, list)
        assert "filesystem" in backends
        assert len(backends) >= 1