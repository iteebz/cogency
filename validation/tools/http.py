#!/usr/bin/env python3
"""HTTP validation."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from util import multi_test_validation

from cogency.tools import HTTP


async def main():
    """HTTP tool validation."""
    tests = [
        ("Make a GET request to httpbin.org/json", ["json", "data"]),
        ("Fetch the status code from httpbin.org/status/200", ["200"]),
        ("Make a request and show the response headers", ["header", "content-type"]),
    ]

    success = await multi_test_validation(
        "HTTP", "HTTP requests and response handling", tests, tools=[HTTP()]
    )

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
