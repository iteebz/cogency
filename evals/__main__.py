"""Evals CLI entry point."""

import asyncio

from .eval import cli

if __name__ == "__main__":
    asyncio.run(cli())
