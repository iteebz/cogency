"""Test multi-user isolation functionality."""
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock
from cogency.memory.backends.filesystem import FilesystemBackend
from cogency.memory.core import MemoryType
from cogency.context import Context
from cogency.agent import Agent
from cogency.tools.recall import RecallTool


class TestMultiUserIsolation:
    """Test multi-user isolation in cogency."""
    
    @pytest.fixture
    def temp_memory_dir(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def memory(self, temp_memory_dir):
        """Create FSMemory instance for testing."""
        return FilesystemBackend(temp_memory_dir)
    
    @pytest.mark.asyncio
    async def test_memory_user_isolation(self, memory):
        """Test that memory is isolated per user."""
        # Store content for user1
        await memory.memorize("User1 personal info", user_id="user1", tags=["personal"])
        
        # Store content for user2
        await memory.memorize("User2 personal info", user_id="user2", tags=["personal"])
        
        # Test user1 can only see their content
        user1_results = await memory.recall("personal info", user_id="user1")
        assert len(user1_results) == 1
        assert "User1" in user1_results[0].content
        
        # Test user2 can only see their content
        user2_results = await memory.recall("personal info", user_id="user2")
        assert len(user2_results) == 1
        assert "User2" in user2_results[0].content
        
        # Test default user doesn't see either
        default_results = await memory.recall("personal info", user_id="default")
        assert len(default_results) == 0
    
    @pytest.mark.asyncio
    async def test_memory_directory_structure(self, memory):
        """Test that user-specific directories are created."""
        base_dir = Path(memory.base_memory_dir)
        
        # Store content for different users
        await memory.memorize("Content for user1", user_id="user1")
        await memory.memorize("Content for user2", user_id="user2")
        
        # Check directory structure
        user1_dir = base_dir / "user1"
        user2_dir = base_dir / "user2"
        
        assert user1_dir.exists()
        assert user2_dir.exists()
        
        # Check files are in correct directories
        user1_files = list(user1_dir.glob("*.json"))
        user2_files = list(user2_dir.glob("*.json"))
        
        assert len(user1_files) == 1
        assert len(user2_files) == 1
    
    @pytest.mark.asyncio
    async def test_memory_cache_isolation(self, memory):
        """Test that memory cache is isolated per user."""
        # Store identical query for different users
        await memory.memorize("Common content", user_id="user1")
        await memory.memorize("Different content", user_id="user2")
        
        # First recall should populate cache
        user1_results = await memory.recall("content", user_id="user1")
        user2_results = await memory.recall("content", user_id="user2")
        
        # Verify results are different
        assert len(user1_results) == 1
        assert len(user2_results) == 1
        assert user1_results[0].content != user2_results[0].content
        
        # Second recall should use cache but still be isolated
        user1_results2 = await memory.recall("content", user_id="user1")
        user2_results2 = await memory.recall("content", user_id="user2")
        
        assert user1_results2[0].content == user1_results[0].content
        assert user2_results2[0].content == user2_results[0].content
    
    @pytest.mark.asyncio
    async def test_memory_tool_isolation(self, memory):
        """Test that memory tools are isolated per user."""
        memorize_tool = MemorizeTool(memory)
        recall_tool = RecallTool(memory)
        
        # Create contexts for different users
        user1_context = Context("Test input", user_id="user1")
        user2_context = Context("Test input", user_id="user2")
        
        # Store content using tools
        await memorize_tool.run(
            content="User1 secret", 
            _context=user1_context
        )
        await memorize_tool.run(
            content="User2 secret", 
            _context=user2_context
        )
        
        # Test recall isolation
        user1_result = await recall_tool.run(
            query="secret", 
            _context=user1_context
        )
        user2_result = await recall_tool.run(
            query="secret", 
            _context=user2_context
        )
        
        assert user1_result["success"] is True
        assert user2_result["success"] is True
        assert len(user1_result["results"]) == 1
        assert len(user2_result["results"]) == 1
        assert "User1" in user1_result["results"][0]["content"]
        assert "User2" in user2_result["results"][0]["content"]
    
    @pytest.mark.asyncio
    async def test_context_user_isolation(self):
        """Test that context maintains user isolation."""
        # Create contexts for different users
        user1_context = Context("Query 1", user_id="user1")
        user2_context = Context("Query 2", user_id="user2")
        
        # Add messages to contexts
        user1_context.add_message("user", "Hello from user1")
        user2_context.add_message("user", "Hello from user2")
        
        # Verify isolation
        assert user1_context.user_id == "user1"
        assert user2_context.user_id == "user2"
        assert user1_context.messages != user2_context.messages
    
    @pytest.mark.asyncio
    async def test_agent_user_context_isolation(self):
        """Test that agent maintains separate contexts per user."""
        # Create mock LLM
        mock_llm = Mock()
        mock_llm.invoke = AsyncMock(return_value="Mock response")
        
        # Create agent with conversation history enabled
        agent = Agent(
            name="test_agent",
            llm=mock_llm,
            conversation_history=True
        )
        
        # Get contexts for different users
        user1_context = agent._get_user_context("user1", "Query 1")
        user2_context = agent._get_user_context("user2", "Query 2")
        
        # Verify isolation
        assert user1_context.user_id == "user1"
        assert user2_context.user_id == "user2"
        assert user1_context.current_input == "Query 1"
        assert user2_context.current_input == "Query 2"
        
        # Verify contexts are stored separately
        assert "user1" in agent.user_contexts
        assert "user2" in agent.user_contexts
        assert agent.user_contexts["user1"] is user1_context
        assert agent.user_contexts["user2"] is user2_context
    
    @pytest.mark.asyncio
    async def test_memory_clear_user_isolation(self, memory):
        """Test that clearing memory is isolated per user."""
        # Store content for both users
        await memory.memorize("User1 content", user_id="user1")
        await memory.memorize("User2 content", user_id="user2")
        
        # Clear only user1's memory
        await memory.clear(user_id="user1")
        
        # Verify user1's memory is cleared
        user1_results = await memory.recall("content", user_id="user1")
        assert len(user1_results) == 0
        
        # Verify user2's memory is intact
        user2_results = await memory.recall("content", user_id="user2")
        assert len(user2_results) == 1
        assert "User2" in user2_results[0].content
    
    @pytest.mark.asyncio
    async def test_memory_forget_user_isolation(self, memory):
        """Test that forgetting artifacts is isolated per user."""
        # Store content for both users
        user1_artifact = await memory.memorize("User1 content", user_id="user1")
        user2_artifact = await memory.memorize("User2 content", user_id="user2")
        
        # Try to forget user1's artifact as user2 (should fail)
        user2_forget_result = await memory.forget(user1_artifact.id, user_id="user2")
        assert user2_forget_result is False
        
        # Verify user1's content still exists
        user1_results = await memory.recall("content", user_id="user1")
        assert len(user1_results) == 1
        
        # Forget user1's artifact as user1 (should succeed)
        user1_forget_result = await memory.forget(user1_artifact.id, user_id="user1")
        assert user1_forget_result is True
        
        # Verify user1's content is gone
        user1_results = await memory.recall("content", user_id="user1")
        assert len(user1_results) == 0
        
        # Verify user2's content is intact
        user2_results = await memory.recall("content", user_id="user2")
        assert len(user2_results) == 1