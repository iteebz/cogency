#!/usr/bin/env python3
"""CLI interface for cogency agent."""

import argparse
import sys

from cogency.agent import Agent
from cogency.config import get_config
from cogency.llm import GeminiLLM
from cogency.tools.calculator import CalculatorTool
from cogency.tools.file_manager import FileManagerTool
from cogency.tools.web_search import WebSearchTool
from cogency.utils.formatting import format_trace


def create_llm() -> GeminiLLM:
    """Create LLM instance from configuration."""
    config = get_config()

    return GeminiLLM(
        api_keys=config.api_keys,
        model=config.model,
        timeout=config.timeout,
        temperature=config.temperature,
    )


def create_tools():
    """Create tool instances from configuration."""
    config = get_config()

    tools = [
        CalculatorTool(),
        FileManagerTool(base_dir=config.file_base_dir),
        WebSearchTool(),
    ]

    return tools


def interactive_mode(agent: Agent, enable_trace: bool = False):
    """Run agent in interactive mode."""
    print("🤖 Cogency Agent - Interactive Mode")
    print("Type 'exit' or 'quit' to stop, 'trace' to toggle tracing")
    print("-" * 50)

    while True:
        try:
            message = input("\n> ").strip()

            if message.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break

            if message.lower() == "trace":
                enable_trace = not enable_trace
                print(f"Tracing {'enabled' if enable_trace else 'disabled'}")
                continue

            if not message:
                continue

            result = agent.run(message, enable_trace=enable_trace)
            print(f"🤖 {result['response']}")

            if enable_trace and "execution_trace" in result:
                print(format_trace(result["execution_trace"]))

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Run the Cogency agent.")
    parser.add_argument(
        "message",
        nargs="?",
        help="Message to send to the agent (for non-interactive mode).",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Run the agent in interactive mode.",
    )
    parser.add_argument(
        "-t", "--trace", action="store_true", help="Enable tracing for agent execution."
    )
    args = parser.parse_args()

    # Load configuration
    try:
        config = get_config()
    except Exception as e:
        print(f"Configuration error: {e}")
        sys.exit(1)

    # Create agent
    try:
        llm = create_llm()
        tools = create_tools()
        agent = Agent(name=config.agent_name, llm=llm, tools=tools, max_depth=config.max_depth)
    except Exception as e:
        print(f"Error initializing agent: {e}")
        sys.exit(1)

    # Use trace setting from CLI
    enable_trace = args.trace
    print_trace = args.trace

    # Interactive mode
    if args.interactive or not args.message:
        interactive_mode(agent, enable_trace)
        return

    # Single query mode
    try:
        result = agent.run(args.message, enable_trace=enable_trace, print_trace=print_trace)
        if not print_trace:  # Don't double-print if already printed during execution
            print("Response:", result["response"])

        if enable_trace and not print_trace and "execution_trace" in result:
            print(format_trace(result["execution_trace"]))

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
