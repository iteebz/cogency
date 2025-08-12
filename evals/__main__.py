"""Evaluation system entry point."""

import asyncio

from .runner import main

if __name__ == "__main__":
    asyncio.run(main())
