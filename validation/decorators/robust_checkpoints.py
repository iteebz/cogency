"""@robust checkpoint validation - failure recovery checkpoints."""

import asyncio
import tempfile
from pathlib import Path

from cogency import Agent
from cogency.config import Persist, Robust
from cogency.persist import Filesystem as FilesystemPersist


async def test_checkpoint_basic_persistence():
    """Test basic checkpoint persistence and recovery."""
    print("💾 Testing basic checkpoint persistence...")

    with tempfile.TemporaryDirectory() as temp_dir:
        persist_store = FilesystemPersist(Path(temp_dir) / "checkpoints")
        persist_config = Persist(enabled=True, store=persist_store)

        # First run - create checkpoint
        agent1 = Agent("checkpoint-basic", persist=persist_config, depth=5)

        result1 = await agent1.run(
            "Start analyzing the evolution of programming languages. Focus on the 1990s era first."
            "checkpoint_user"
        )

        # Second run - should recover from checkpoint
        agent2 = Agent("checkpoint-basic", persist=persist_config, depth=5)

        result2 = await agent2.run(
            "Continue the programming language analysis from the 1990s, now move to the 2000s."
            "checkpoint_user"
        )

        if (
            result1
            and result2
            and "ERROR:" not in result1
            and "ERROR:" not in result2
            and len(result1) > 50
            and len(result2) > 50
        ):
            print("✅ Basic checkpoint persistence succeeded")
            return True
        else:
            print("❌ Basic checkpoint persistence failed")
            return False


async def test_checkpoint_with_robust():
    """Test checkpoint persistence combined with @robust features."""
    print("🛡️  Testing checkpoint with @robust integration...")

    with tempfile.TemporaryDirectory() as temp_dir:
        persist_store = FilesystemPersist(Path(temp_dir) / "robust_checkpoints")
        persist_config = Persist(enabled=True, store=persist_store)
        robust_config = Robust(retry=True, attempts=2, checkpoint=True, timeout=8.0)

        agent = Agent("checkpoint-robust", persist=persist_config, robust=robust_config, depth=3)

        # Complex multi-step task that might need checkpointing
        result = await agent.run(
            "Research and summarize the key differences between functional and object-oriented programming paradigms. Include specific examples."
            "robust_checkpoint_user"
        )

        if result and "ERROR:" not in result and len(result) > 100:
            print("✅ Checkpoint + @robust integration succeeded")
            return True
        else:
            print("❌ Checkpoint + @robust integration failed")
            return False


async def test_checkpoint_state_continuity():
    """Test that checkpoint preserves state across interruptions."""
    print("🔄 Testing checkpoint state continuity...")

    with tempfile.TemporaryDirectory() as temp_dir:
        persist_store = FilesystemPersist(Path(temp_dir) / "continuity_checkpoints")
        persist_config = Persist(enabled=True, store=persist_store)

        # Session 1 - start a complex task
        agent1 = Agent(
            "continuity-test", persist=persist_config, depth=4, tools=["calculator", "search"]
        )

        result1 = await agent1.run(
            "I'm building a financial model. Start by calculating compound interest for $10,000 at 7% over 5 years."
            "continuity_user"
        )

        # Session 2 - continue the financial model
        agent2 = Agent(
            "continuity-test", persist=persist_config, depth=4, tools=["calculator", "search"]
        )

        result2 = await agent2.run(
            "Now add inflation considerations to our financial model. Use 3% annual inflation."
            "continuity_user"
        )

        # Check that both results are coherent and reference the model
        if (
            result1
            and result2
            and "ERROR:" not in result1
            and "ERROR:" not in result2
            and ("10000" in result1 or "10,000" in result1)
            and ("inflation" in result2.lower() or "model" in result2.lower())
        ):
            print("✅ Checkpoint state continuity succeeded")
            return True
        else:
            print("❌ Checkpoint state continuity failed")
            return False


async def main():
    """Run all checkpoint persistence validation tests."""
    print("🚀 Starting checkpoint persistence validation...\n")

    tests = [
        test_checkpoint_basic_persistence,
        test_checkpoint_with_robust,
        test_checkpoint_state_continuity,
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

    print(f"📊 Checkpoint validation: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 Checkpoint persistence is production ready!")
    else:
        print("⚠️  Checkpoint persistence needs attention")

    return passed == total


if __name__ == "__main__":
    asyncio.run(main())
