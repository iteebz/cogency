"""CLI interface."""

import argparse
import asyncio
import sys
from pathlib import Path


async def interactive_mode(agent) -> None:
    """Interactive chat mode."""
    print("Cogency Agent")
    print("Type 'exit' to quit")
    print("-" * 30)

    while True:
        try:
            message = input("\n> ").strip()
            if message.lower() in ["exit", "quit"]:
                break
            if message:
                await agent.run_async(message)
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"✗ Error: {e}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Cogency - Zero ceremony cognitive agents")
    parser.add_argument("message", nargs="*", help="Message for agent")
    parser.add_argument("-i", "--interactive", action="store_true", help="Interactive mode")
    args = parser.parse_args()

    # Setup agent
    from cogency import Agent
    from cogency.tools import Files, Recall, Scrape, Search, Shell

    tools = [Files(), Shell(), Search(), Scrape(), Recall()]

    # Add Retrieval if configured
    import os
    if retrieval_path := os.getenv("COGENCY_RETRIEVAL_PATH"):
        from cogency.tools import Retrieval
        embeddings_file = Path(retrieval_path).expanduser() / "embeddings.json"
        tools.append(Retrieval(embeddings_path=str(embeddings_file)))

    try:
        agent = Agent("assistant", tools=tools, memory=True)
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

    # Run
    message = " ".join(args.message) if args.message else ""
    if args.interactive or not message:
        asyncio.run(interactive_mode(agent))
    else:
        try:
            asyncio.run(agent.run_async(message))
        except Exception as e:
            print(f"✗ Error: {e}")


if __name__ == "__main__":
    main()