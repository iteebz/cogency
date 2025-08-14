"""Minimal CLI for agent interaction."""

import asyncio
import sys


async def main():
    """Minimal CLI interface."""
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help"]:
        print("usage: cogency {ask,chat}")
        print("")
        print("commands:")
        print("  ask MESSAGE    One-shot query")
        print("  chat          Interactive mode")
        print("")
        print("debug utilities in scripts/ directory")
        return

    if sys.argv[1] == "--version":
        print("cogency 1.3.0")
        return

    command = sys.argv[1]

    if command == "ask":
        if len(sys.argv) < 3:
            print("usage: cogency ask 'Your question'")
            return
        message = " ".join(sys.argv[2:])

        from cogency import Agent

        agent = Agent("assistant")
        response = await agent.run_async(message)
        print(response)

    elif command == "chat":
        from cogency.cli.interactive import interactive_mode

        await interactive_mode()

    else:
        print(f"unknown command: {command}")
        print("available: ask, chat")
        print("debug utilities in scripts/ directory")


def cli_main():
    """Entry point for CLI."""
    asyncio.run(main())


if __name__ == "__main__":
    cli_main()
