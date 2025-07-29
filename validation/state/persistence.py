"""State persistence validation - multitenancy and memory management."""

import asyncio
import tempfile
from pathlib import Path

from cogency import Agent
from cogency.config import Persist
from cogency.persist import FilesystemPersist


async def test_state_multitenancy():
    """Test state isolation between different users."""
    print("👥 Testing state multitenancy...")

    with tempfile.TemporaryDirectory() as temp_dir:
        persist_store = FilesystemPersist(Path(temp_dir) / "multitenancy")
        persist_config = Persist(enabled=True, store=persist_store)

        agent = Agent("multitenancy-test", persist=persist_config, debug=True)

        # User 1 stores information
        result1 = await agent.run(
            "My name is Alice and I work as a software engineer", user_id="user1"
        )

        # User 2 stores different information
        result2 = await agent.run("My name is Bob and I work as a data scientist", user_id="user2")

        # User 1 retrieves their information
        result3 = await agent.run("What is my name and job?", user_id="user1")

        # User 2 retrieves their information
        result4 = await agent.run("What is my name and job?", user_id="user2")

        if (
            all(r and "ERROR:" not in r for r in [result1, result2, result3, result4])
            and "alice" in result3.lower()
            and "engineer" in result3.lower()
            and "bob" in result4.lower()
            and "scientist" in result4.lower()
        ):
            print("✅ State multitenancy succeeded")
            return True
        else:
            print("❌ State multitenancy failed")
            return False


async def test_state_memory_cleanup():
    """Test that state doesn't grow unbounded."""
    print("🧹 Testing state memory cleanup...")

    with tempfile.TemporaryDirectory() as temp_dir:
        persist_store = FilesystemPersist(Path(temp_dir) / "cleanup")
        persist_config = Persist(enabled=True, store=persist_store)

        agent = Agent(
            "cleanup-test",
            persist=persist_config,
            depth=3,  # Limited depth for cleanup testing
            debug=False,
        )

        # Generate multiple conversations
        initial_state_count = len(agent.user_states)

        for i in range(5):
            await agent.run(f"This is conversation {i}", user_id=f"user_{i}")

        # Check state management
        final_state_count = len(agent.user_states)

        # Should have some states but not grow indefinitely
        if final_state_count > initial_state_count and final_state_count <= 10:
            print("✅ State memory management working")
            return True
        else:
            print("❌ State memory management failed")
            return False


async def test_state_persistence_recovery():
    """Test state recovery after agent restart."""
    print("🔄 Testing state persistence recovery...")

    with tempfile.TemporaryDirectory() as temp_dir:
        persist_store = FilesystemPersist(Path(temp_dir) / "recovery")
        persist_config = Persist(enabled=True, store=persist_store)

        # Agent 1 - store conversation state
        agent1 = Agent("recovery-test", persist=persist_config, debug=True)

        result1 = await agent1.run(
            "I'm planning a trip to Japan. I want to visit Tokyo first.", user_id="traveler"
        )

        # Agent 2 - simulate restart, should recover state
        agent2 = Agent("recovery-test", persist=persist_config, debug=True)

        result2 = await agent2.run(
            "What was my travel destination and which city did I want to visit first?",
            user_id="traveler",
        )

        if (
            result1
            and result2
            and "ERROR:" not in result1
            and "ERROR:" not in result2
            and ("japan" in result2.lower() and "tokyo" in result2.lower())
        ):
            print("✅ State persistence recovery succeeded")
            return True
        else:
            print("❌ State persistence recovery failed")
            return False


async def test_state_concurrent_users():
    """Test concurrent state handling for multiple users."""
    print("⚡ Testing concurrent state handling...")

    with tempfile.TemporaryDirectory() as temp_dir:
        persist_store = FilesystemPersist(Path(temp_dir) / "concurrent")
        persist_config = Persist(enabled=True, store=persist_store)

        agent = Agent("concurrent-test", persist=persist_config, debug=False)

        # Concurrent requests from different users
        tasks = [
            agent.run(f"My favorite color is color_{i}", user_id=f"user_{i}") for i in range(3)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should succeed without interference
        successful = [r for r in results if isinstance(r, str) and "ERROR:" not in r]

        if len(successful) == 3:
            print("✅ Concurrent state handling succeeded")
            return True
        else:
            print("❌ Concurrent state handling failed")
            return False


async def main():
    """Run all state persistence validation tests."""
    print("🚀 Starting state persistence validation...\n")

    tests = [
        test_state_multitenancy,
        test_state_memory_cleanup,
        test_state_persistence_recovery,
        test_state_concurrent_users,
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

    print(f"📊 State persistence validation: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 State persistence is production ready!")
    else:
        print("⚠️  State persistence needs attention")

    return passed == total


if __name__ == "__main__":
    asyncio.run(main())
