"""Magical CLI that just works."""

import argparse
import asyncio
import sys


async def interactive_mode(agent) -> None:
    """Interactive mode with magical DX."""
    print("🤖 Cogency Agent")
    print("Type 'exit' to quit")
    print("-" * 30)

    while True:
        try:
            message = input("\n> ").strip()

            if message.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break

            if not message:
                continue

            response = await agent.run(message)
            print(f"🤖 {response}")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def trace_args() -> bool:
    """Parse trace argument from CLI and return trace flag."""
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--trace", action="store_true", help="Enable detailed tracing output")
    args = parser.parse_args()
    return args.trace


def main():
    """Magical CLI entry point."""
    parser = argparse.ArgumentParser(description="Run Cogency agent")
    parser.add_argument("message", nargs="?", help="Message for agent")
    parser.add_argument("-i", "--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("-t", "--trace", action="store_true", help="Enable detailed tracing output")
    args = parser.parse_args()

    # Lazy import to avoid circular dependency
    from cogency import Agent

    try:
        agent = Agent("assistant", trace=args.trace)  # Auto-detects everything
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    if args.interactive or not args.message:
        asyncio.run(interactive_mode(agent))
    else:
        try:
            response = asyncio.run(agent.run(args.message))
            print(response)
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
