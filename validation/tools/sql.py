#!/usr/bin/env python3
"""SQL validation."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from util import multi_test_validation

from cogency.tools import SQL


async def main():
    """SQL tool validation."""
    tests = [
        ("Create a simple table with id and name columns", ["CREATE", "TABLE", "id", "name"]),
        ("Insert a record into the table", ["INSERT", "record"]),
        ("Query all records from the table", ["SELECT", "FROM"]),
    ]

    success = await multi_test_validation("SQL", "SQL database operations", tests, tools=[SQL()])

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
