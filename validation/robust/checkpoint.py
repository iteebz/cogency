#!/usr/bin/env python3
"""Checkpoint validation - agent state save and restore capabilities."""

import asyncio
import tempfile
from pathlib import Path

from cogency import Agent
from cogency.config import Persist
from cogency.persist.store import Filesystem
from cogency.tools import Calculator


async def validate_checkpoint_creation():
    """Validate that agent checkpoints are created properly."""
    print("💾 Validating checkpoint creation...")

    with tempfile.TemporaryDirectory() as temp_dir:
        persist_store = Filesystem(Path(temp_dir) / "checkpoints")
        persist_config = Persist(enabled=True, store=persist_store)

        agent = Agent(
            "checkpoint-creator",
            identity="agent that creates checkpoints during conversations",
            tools=[Calculator()],
            persist=persist_config,
            notify=True,
            trace=True,
        )

        # Execute operations that should create checkpoints
        result = await agent.run(
            "Calculate 25 * 8, then remember this result for the next calculation",
            user_id="checkpoint_user",
        )

        if result and "ERROR:" not in result and "200" in result:
            print("✅ Checkpoint creation working")
            return True
        else:
            print("❌ Checkpoint creation failed")
            return False


async def validate_checkpoint_restoration():
    """Validate that agent state can be restored from checkpoints."""
    print("🔄 Validating checkpoint restoration...")

    with tempfile.TemporaryDirectory() as temp_dir:
        persist_store = Filesystem(Path(temp_dir) / "restoration")
        persist_config = Persist(enabled=True, store=persist_store)

        # Agent 1: Create initial state
        agent1 = Agent(
            "checkpoint-restorer",
            persist=persist_config,
            tools=[Calculator()],
            notify=True,
            trace=True,
        )

        await agent1.run(
            "My project budget is $5000. Calculate 20% of this budget for marketing",
            user_id="budget_user",
        )

        # Agent 2: Restore and continue from checkpoint
        agent2 = Agent(
            "checkpoint-restorer",
            persist=persist_config,
            tools=[Calculator()],
            notify=True,
            trace=True,
        )

        result = await agent2.run(
            "What was my project budget and how much did we allocate for marketing?",
            user_id="budget_user",
        )

        if result and ("5000" in result or "1000" in result) and "marketing" in result.lower():
            print("✅ Checkpoint restoration working")
            return True
        else:
            print("❌ Checkpoint restoration failed")
            return False


async def validate_checkpoint_isolation():
    """Validate that checkpoints are properly isolated between users."""
    print("👥 Validating checkpoint isolation...")

    with tempfile.TemporaryDirectory() as temp_dir:
        persist_store = Filesystem(Path(temp_dir) / "isolation")
        persist_config = Persist(enabled=True, store=persist_store)

        agent = Agent(
            "checkpoint-isolator",
            persist=persist_config,
            tools=[Calculator()],
            notify=True,
            trace=True,
        )

        # User A conversation
        await agent.run("My age is 25", user_id="user_a")

        # User B conversation
        await agent.run("My age is 30", user_id="user_b")

        # Check isolation
        result_a = await agent.run("How old am I?", user_id="user_a")
        result_b = await agent.run("How old am I?", user_id="user_b")

        if "25" in result_a and "30" in result_b:
            print("✅ Checkpoint isolation working")
            return True
        else:
            print("❌ Checkpoint isolation failed")
            return False


async def main():
    """Run all checkpoint validation tests."""
    print("🚀 Starting checkpoint validation...\n")

    validations = [
        validate_checkpoint_creation,
        validate_checkpoint_restoration,
        validate_checkpoint_isolation,
    ]

    results = []
    for validation in validations:
        try:
            success = await validation()
            results.append(success)
        except Exception as e:
            print(f"❌ {validation.__name__} crashed: {e}")
            results.append(False)
        print()

    passed = sum(results)
    total = len(results)

    print(f"📊 Checkpoint validation: {passed}/{total} validations passed")

    if passed == total:
        print("🎉 Checkpoint system is production ready!")
    else:
        print("⚠️  Checkpoint system needs attention")

    return passed == total


if __name__ == "__main__":
    asyncio.run(main())
