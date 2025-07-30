#!/usr/bin/env python3
"""Time validation."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from util import multi_test_validation

from cogency.tools import Time


async def main():
    """Time tool validation."""
    tests = [
        ("What time is it now?", ["time", "now"]),
        ("Convert 3 PM to 24-hour format", ["15", "24-hour"]),
        ("Calculate the time difference between 2 PM and 5 PM", ["3", "hour", "difference"]),
    ]

    success = await multi_test_validation(
        "Time", "Time calculations and formatting", tests, tools=[Time()]
    )

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
