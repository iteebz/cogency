#!/usr/bin/env python3
"""Shell validation."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from util import multi_test_validation

from cogency.tools import Shell


async def main():
    """Shell tool validation."""
    tests = [
        ("List the files in the current directory", ["ls", "file"]),
        ("Show the current working directory", ["pwd", "directory"]),
        ("Echo 'Hello World' to the terminal", ["Hello", "World", "echo"]),
    ]

    success = await multi_test_validation(
        "Shell", "Shell command execution", tests, tools=[Shell()]
    )

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
