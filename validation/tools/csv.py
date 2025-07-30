#!/usr/bin/env python3
"""CSV validation."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from util import multi_test_validation

from cogency.tools import CSV


async def main():
    """CSV tool validation."""
    tests = [
        (
            "Create a CSV with columns 'name' and 'age' containing data for Alice (25) and Bob (30)",
            ["Alice", "Bob", "25", "30"],
        ),
        ("Read and analyze the structure of a CSV file", ["column", "row"]),
        ("Filter CSV data to show only entries where age is greater than 25", ["filter", "age"]),
    ]

    success = await multi_test_validation(
        "CSV", "CSV file creation, reading, and manipulation", tests, tools=[CSV()]
    )

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
