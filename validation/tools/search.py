#!/usr/bin/env python3
"""Search validation."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from util import multi_test_validation

from cogency.tools import Search


async def main():
    """Search tool validation."""
    tests = [
        ("Search for information about Python programming", ["Python", "programming"]),
        ("Find recent news about artificial intelligence", ["AI", "artificial", "intelligence"]),
        ("Search for the latest updates on machine learning", ["machine", "learning"]),
    ]

    success = await multi_test_validation(
        "Search", "Web search and information retrieval", tests, tools=[Search()]
    )

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
