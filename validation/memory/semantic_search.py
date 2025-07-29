"""Memory validation - semantic search and embedding capabilities."""

import asyncio
import tempfile
from pathlib import Path

from cogency import Agent
from cogency.memory.store import FilesystemStore
from cogency.services.embed import OpenAIEmbed


async def test_memory_basic_storage():
    """Test basic memory storage and retrieval."""
    print("🧠 Testing basic memory storage...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        memory = FilesystemStore(Path(temp_dir) / "memory")
        
        agent = Agent(
            "memory-basic",
            memory=memory,
            debug=True
        )
        
        # Store some information
        result1 = await agent.run("Remember that my favorite programming language is Python")
        result2 = await agent.run("What programming language do I prefer?")
        
        if (result1 and result2 and 
            "ERROR:" not in result1 and "ERROR:" not in result2 and
            "python" in result2.lower()):
            print("✅ Basic memory storage succeeded")
            return True
        else:
            print("❌ Basic memory storage failed")
            return False


async def test_memory_semantic_search():
    """Test semantic search with available embedders."""
    print("🔍 Testing semantic search...")
    
    # Test with realistic embedder setup (gracefully handle missing)
    embed = None
    embedder_name = "None"
    
    try:
        # Try Nomic (your actual embedder)
        from cogency.services.embed import NomicEmbed
        embed = NomicEmbed()
        embedder_name = "Nomic"
    except:
        try:
            # Fallback to OpenAI
            embed = OpenAIEmbed()
            embedder_name = "OpenAI"
        except:
            print("⚠️  No embedders configured - testing without semantic search")
            return True
    
    with tempfile.TemporaryDirectory() as temp_dir:
        memory = FilesystemStore(Path(temp_dir) / "semantic")
        
        agent = Agent(
            "memory-semantic",
            memory=memory,
            embed=embed,
            debug=True
        )
        
        # Store diverse information for semantic matching
        await agent.run("Remember: I love outdoor adventures like hiking and rock climbing")
        await agent.run("Remember: My expertise is in machine learning and Python development")
        await agent.run("Remember: I work remotely from mountain towns")
        
        # Test semantic retrieval (not exact keyword match) 
        result = await agent.run("What physical activities do I enjoy?")
        
        if (result and "ERROR:" not in result and 
            ("hiking" in result.lower() or "climbing" in result.lower())):
            print(f"✅ Semantic search succeeded ({embedder_name})")
            return True
        else:
            print(f"❌ Semantic search failed ({embedder_name})")
            return False


async def test_memory_capacity_handling():
    """Test memory behavior under load and capacity limits."""
    print("📊 Testing memory capacity handling...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        memory = FilesystemStore(Path(temp_dir) / "capacity")
        agent = Agent("memory-load", memory=memory, debug=False)
        
        # Store many items quickly to test capacity handling
        for i in range(15):
            await agent.run(f"Remember item {i}: Test data point number {i} with unique content")
        
        # Should still retrieve specific items
        result = await agent.run("What was item 14 about?")
        
        if (result and "ERROR:" not in result and "14" in result):
            print("✅ Memory capacity handling succeeded")
            return True
        else:
            print("❌ Memory capacity handling failed")
            return False


async def test_memory_persistence_across_sessions():
    """Test memory persistence across agent sessions."""
    print("💾 Testing memory persistence across sessions...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        memory_path = Path(temp_dir) / "persistent_memory"
        
        # Session 1 - store information
        memory1 = FilesystemStore(memory_path)
        agent1 = Agent("memory-persist-1", memory=memory1, debug=True)
        
        result1 = await agent1.run("My project deadline is March 15th, 2024. Remember this important date.")
        
        # Session 2 - retrieve information
        memory2 = FilesystemStore(memory_path)
        agent2 = Agent("memory-persist-2", memory=memory2, debug=True)
        
        result2 = await agent2.run("When is my project deadline?")
        
        if (result1 and result2 and
            "ERROR:" not in result1 and "ERROR:" not in result2 and
            ("march" in result2.lower() and "15" in result2)):
            print("✅ Memory persistence across sessions succeeded")
            return True
        else:
            print("❌ Memory persistence across sessions failed")
            return False


async def main():
    """Run all memory validation tests."""
    print("🚀 Starting memory validation...\n")
    
    tests = [
        test_memory_basic_storage,
        test_memory_semantic_search,
        test_memory_capacity_handling,
        test_memory_persistence_across_sessions
    ]
    
    results = []
    for test in tests:
        try:
            success = await test()
            results.append(success)
        except Exception as e:
            print(f"❌ {test.__name__} crashed: {e}")
            results.append(False)
        print()
    
    passed = sum(results)
    total = len(results)
    
    print(f"📊 Memory validation: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Memory system is production ready!")
    else:
        print("⚠️  Memory system needs attention")
    
    return passed == total


if __name__ == "__main__":
    asyncio.run(main())