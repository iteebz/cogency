"""Evals CLI entry point."""

import asyncio

from .eval import cli


def main():
    """Entry point for poetry script."""
    asyncio.run(cli())


if __name__ == "__main__":
    main()
