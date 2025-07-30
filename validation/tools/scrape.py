#!/usr/bin/env python3
"""Scrape validation."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from util import multi_test_validation

from cogency.tools import Scrape


async def main():
    """Scrape tool validation."""
    tests = [
        ("Scrape the title from example.com", ["Example", "title"]),
        ("Extract the main heading from a simple webpage", ["heading", "h1"]),
        ("Get the text content from a basic HTML page", ["text", "content"]),
    ]

    success = await multi_test_validation(
        "Scrape", "Web scraping and content extraction", tests, tools=[Scrape()]
    )

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
