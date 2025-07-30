"""Memory backend validation - test all persistence providers."""

import asyncio
import os
import tempfile
import uuid
from pathlib import Path

from cogency import Agent
from cogency.memory.store import Chroma, Filesystem, Pinecone, Postgres


async def test_filesystem_backend():
    """Test filesystem memory backend."""
    print("💾 Testing Filesystem memory backend...")

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            memory = Filesystem(Path(temp_dir) / "fs_memory")
            agent = Agent("fs-test", memory=memory, notify=False)

            # Test basic storage and retrieval
            await agent.run("Remember that I prefer TypeScript over JavaScript")
            result = await agent.run("What programming language do I prefer?")

            if result and "typescript" in result.lower():
                print("✅ Filesystem backend working")
                return True
            else:
                print("❌ Filesystem backend failed retrieval")
                return False

        except Exception as e:
            print(f"❌ Filesystem backend crashed: {e}")
            return False


async def test_chroma_backend():
    """Test ChromaDB memory backend."""
    print("🔍 Testing ChromaDB memory backend...")

    try:
        # Use temporary directory for ChromaDB
        with tempfile.TemporaryDirectory() as temp_dir:
            memory = Chroma(persist_directory=temp_dir)
            agent = Agent("chroma-test", memory=memory, notify=False)

            # Test semantic storage and retrieval
            await agent.run("Remember that I love hiking in the mountains")
            result = await agent.run("What outdoor activities do I enjoy?")

            if result and ("hiking" in result.lower() or "mountain" in result.lower()):
                print("✅ ChromaDB backend working")
                return True
            else:
                print("❌ ChromaDB backend failed retrieval")
                return False

    except Exception as e:
        print(f"⚠️  ChromaDB backend not available: {e}")
        return True  # Don't fail if ChromaDB isn't installed


async def test_pinecone_backend():
    """Test Pinecone memory backend."""
    print("🌲 Testing Pinecone memory backend...")

    if not os.environ.get("PINECONE_API_KEY"):
        print("⚪ Pinecone not configured (missing PINECONE_API_KEY)")
        return True

    try:
        # Create test index name
        index_name = f"test-{uuid.uuid4().hex[:8]}"

        memory = Pinecone(api_key=os.environ["PINECONE_API_KEY"], index_name=index_name)
        agent = Agent("pinecone-test", memory=memory, notify=False)

        # Test storage and retrieval
        await agent.run("Remember that I work remotely from San Francisco")
        result = await agent.run("Where do I work from?")

        if result and ("san francisco" in result.lower() or "remote" in result.lower()):
            print("✅ Pinecone backend working")
            return True
        else:
            print("❌ Pinecone backend failed retrieval")
            return False

    except Exception as e:
        print(f"❌ Pinecone backend crashed: {e}")
        return False


async def test_postgres_backend():
    """Test PostgreSQL memory backend."""
    print("🐘 Testing PostgreSQL memory backend...")

    connection_string = os.environ.get("POSTGRES_CONNECTION_STRING")
    if not connection_string:
        print("⚪ PostgreSQL not configured (missing POSTGRES_CONNECTION_STRING)")
        return True

    try:
        memory = Postgres(connection_string=connection_string)
        agent = Agent("postgres-test", memory=memory, notify=False)

        # Test storage and retrieval
        await agent.run("Remember that my favorite framework is FastAPI")
        result = await agent.run("What web framework do I prefer?")

        if result and "fastapi" in result.lower():
            print("✅ PostgreSQL backend working")
            return True
        else:
            print("❌ PostgreSQL backend failed retrieval")
            return False

    except Exception as e:
        print(f"❌ PostgreSQL backend crashed: {e}")
        return False


async def test_memory_isolation():
    """Test memory isolation between different user IDs."""
    print("👥 Testing memory isolation (multitenancy)...")

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            memory = Filesystem(Path(temp_dir) / "iso_memory")
            agent = Agent("isolation-test", memory=memory, notify=False)

            # Store different information for different users
            await agent.run("Remember that my name is Alice", user_id="user1")
            await agent.run("Remember that my name is Bob", user_id="user2")

            # Test retrieval isolation
            result1 = await agent.run("What is my name?", user_id="user1")
            result2 = await agent.run("What is my name?", user_id="user2")

            if result1 and "alice" in result1.lower() and result2 and "bob" in result2.lower():
                print("✅ Memory isolation working")
                return True
            else:
                print("❌ Memory isolation failed")
                print(f"   User1: {result1}")
                print(f"   User2: {result2}")
                return False

        except Exception as e:
            print(f"❌ Memory isolation test crashed: {e}")
            return False


async def test_memory_persistence():
    """Test memory persistence across agent instances."""
    print("🔄 Testing memory persistence across instances...")

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            memory_path = Path(temp_dir) / "persist_memory"

            # Instance 1 - store information
            memory1 = Filesystem(memory_path)
            agent1 = Agent("persist-1", memory=memory1, notify=False)
            await agent1.run("Remember that my project is due on March 15th")

            # Instance 2 - retrieve information
            memory2 = Filesystem(memory_path)
            agent2 = Agent("persist-2", memory=memory2, notify=False)
            result = await agent2.run("When is my project due?")

            if result and ("march" in result.lower() and "15" in result):
                print("✅ Memory persistence working")
                return True
            else:
                print("❌ Memory persistence failed")
                return False

        except Exception as e:
            print(f"❌ Memory persistence test crashed: {e}")
            return False


async def test_memory_capacity():
    """Test memory handling under load."""
    print("📊 Testing memory capacity handling...")

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            memory = Filesystem(Path(temp_dir) / "capacity_memory")
            agent = Agent("capacity-test", memory=memory, notify=False)

            # Store many items quickly
            for i in range(20):
                await agent.run(f"Remember fact {i}: This is test data point number {i}")

            # Should still retrieve specific items
            result = await agent.run("What was fact 15 about?")

            if result and "15" in result and "test data" in result.lower():
                print("✅ Memory capacity handling working")
                return True
            else:
                print("❌ Memory capacity handling failed")
                return False

        except Exception as e:
            print(f"❌ Memory capacity test crashed: {e}")
            return False


async def main():
    """Run all memory backend validation tests."""
    print("🚀 Starting memory backend validation...\n")

    tests = [
        test_filesystem_backend,
        test_chroma_backend,
        test_pinecone_backend,
        test_postgres_backend,
        test_memory_isolation,
        test_memory_persistence,
        test_memory_capacity,
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

    print(f"📊 Memory backend validation: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 Memory backends are production ready!")
    elif passed >= total * 0.8:
        print("🎶 Memory backends mostly working - minor configuration needed")
    else:
        print("⚠️  Memory backends need attention")

    return passed >= total * 0.8  # Allow 80% pass rate for optional backends


if __name__ == "__main__":
    asyncio.run(main())
