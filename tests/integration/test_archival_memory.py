"""Integration tests for archival memory system."""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from resilient_result import Ok

from cogency.memory.archival import ArchivalMemory
from cogency.tools.recall import Recall


class MockLLM:
    async def generate(self, prompt, message=""):
        if "EXISTING DOCUMENT" in prompt and "NEW INSIGHT" in prompt:
            return "# Python Performance\n\n- List comprehensions are fast\n- Numpy is better for numerical work"
        return message or "Test response"


class MockEmbed:
    async def embed(self, text):
        # Return deterministic embeddings for testing
        if "python" in text.lower() and "performance" in text.lower():
            return Ok([[0.9, 0.1, 0.1] + [0.0] * 765])
        elif "python" in text.lower():
            return Ok([[0.8, 0.2, 0.1] + [0.0] * 765])
        else:
            return Ok([[0.1, 0.1, 0.9] + [0.0] * 765])


class TestArchivalMemoryIntegration:
    @pytest.mark.asyncio
    async def test_complete_memory_flow(self):
        """Test end-to-end memory storage, merging, and retrieval."""
        llm = MockLLM()
        embed = MockEmbed()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory"
            archival = ArchivalMemory(llm, embed, str(memory_path))
            
            # Initialize
            await archival.initialize("user1")
            
            # Store first insight
            result1 = await archival.store_insight(
                "user1", "Python", "List comprehensions are faster than loops"
            )
            assert result1.success
            
            # Store second insight (should merge)
            result2 = await archival.store_insight(
                "user1", "Python", "Numpy arrays outperform lists"
            )
            assert result2.success
            
            # Verify file created
            topic_file = memory_path / "user1" / "topics" / "python.md"
            assert topic_file.exists()
            
            content = topic_file.read_text()
            assert "comprehensions" in content.lower()
            assert "numpy" in content.lower()
            
            # Test search functionality
            results = await archival.search_topics(
                "user1", "python performance optimization", min_similarity=0.5
            )
            
            assert len(results) == 1
            assert results[0]["topic"] == "Python"
            assert results[0]["similarity"] > 0.5

    @pytest.mark.asyncio
    async def test_user_isolation(self):
        """Test that user memory is properly isolated."""
        llm = MockLLM()
        embed = MockEmbed()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory"
            archival = ArchivalMemory(llm, embed, str(memory_path))
            
            # Initialize both users
            await archival.initialize("user1")
            await archival.initialize("user2")
            
            # Store insight for user1
            await archival.store_insight("user1", "Python", "Python is great")
            
            # Store insight for user2
            await archival.store_insight("user2", "JavaScript", "JS is flexible")
            
            # User1 should only see Python topics
            user1_results = await archival.search_topics("user1", "programming", min_similarity=0.3)
            user1_topics = [r["topic"] for r in user1_results]
            assert "Python" in user1_topics
            assert "JavaScript" not in user1_topics
            
            # User2 should only see JavaScript topics
            user2_results = await archival.search_topics("user2", "programming", min_similarity=0.3)
            user2_topics = [r["topic"] for r in user2_results]
            assert "JavaScript" in user2_topics
            assert "Python" not in user2_topics

    @pytest.mark.asyncio
    async def test_recall_tool_integration(self):
        """Test Recall integration with ArchivalMemory."""
        llm = MockLLM()
        embed = MockEmbed()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory"
            archival = ArchivalMemory(llm, embed, str(memory_path))
            
            await archival.initialize("user1")
            await archival.store_insight("user1", "Python", "List comprehensions are efficient")
            
            # Setup Recall
            recall_tool = Recall(archival)
            recall_tool.set_context("user1", archival)
            
            # Test recall
            result = await recall_tool.run("python performance", min_similarity=0.5)
            
            assert result.success
            assert result.data["count"] == 1
            assert "Python" in result.data["response"]
            assert "comprehensions" in result.data["response"]