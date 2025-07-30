#!/usr/bin/env python3
"""Calculator validation."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from util import multi_test_validation

from cogency.tools import Calculator


async def main():
    """Calculator tool validation."""
    tests = [
        ("What is 1250 + 850?", ["2100"]),
        ("Calculate (12 * 1.25) + (8 * 0.85)", ["21.8"]),
        ("What's the square root of 64?", ["8"]),
    ]

    success = await multi_test_validation(
        "Calculator", "Basic arithmetic and mathematical operations", tests, tools=[Calculator()]
    )

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
