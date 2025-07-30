#!/usr/bin/env python3
"""Recall validation."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from util import multi_test_validation

from cogency.tools import Recall


async def main():
    """Recall tool validation."""
    tests = [
        ("Remember that my favorite color is blue", ["blue", "remember", "favorite"]),
        ("Store the fact that I work at TechCorp", ["TechCorp", "work", "store"]),
        ("What did I tell you about my favorite color?", ["blue", "favorite", "color"]),
    ]

    success = await multi_test_validation(
        "Recall", "Memory storage and retrieval", tests, tools=[Recall()]
    )

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
