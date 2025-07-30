#!/usr/bin/env python3
"""Date validation."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from util import multi_test_validation

from cogency.tools import Date


async def main():
    """Date tool validation."""
    tests = [
        ("What is today's date?", ["2024", "2025"]),
        ("Calculate the date 30 days from now", ["day"]),
        (
            "What day of the week is it today?",
            ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        ),
    ]

    success = await multi_test_validation(
        "Date", "Date calculations and formatting", tests, tools=[Date()]
    )

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
