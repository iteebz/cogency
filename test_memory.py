"""DEPRECATED: Use tests/test_memory.py for unit tests or validation/memory/impression.py for e2e validation."""

import asyncio


async def test_memory():
    """DEPRECATED: Test moved to proper test directories."""
    print("⚠️  DEPRECATED: This test file has been replaced")
    print("📁 Unit tests: tests/test_memory.py")
    print("🔍 E2E validation: validation/memory/impression.py")
    print("🏃 Run with: poetry run python validation/memory/impression.py")


if __name__ == "__main__":
    asyncio.run(test_memory())
