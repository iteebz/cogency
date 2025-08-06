"""CLI interface."""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


async def interactive_mode(agent) -> None:
    """Interactive chat mode with clean console output."""
    print("Cogency Agent")
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

            # Agent will handle output automatically
            await agent.run_async(message)

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"✗ Error: {e}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Cogency - Zero ceremony cognitive agents")

    # Main arguments
    parser.add_argument("message", nargs="*", help="Message for agent")
    parser.add_argument("-i", "--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("--tools", action="store_true", help="List available tools")
    parser.add_argument("--init", type=str, metavar="NAME", help="Initialize project with NAME")

    args = parser.parse_args()

    # Handle special commands
    if args.tools:
        list_tools()
        return
    elif args.init:
        init_project(args.init)
        return

    # Default agent behavior
    from cogency import Agent
    from cogency.tools import Files, Scrape, Search, Shell

    try:
        agent = Agent(
            "assistant",
            tools=[Files(), Shell(), Search(), Scrape()],
            memory=True,
            identity="You are Cogency, a helpful AI assistant with a knack for getting things done efficiently. Keep responses concise and clear.",
        )
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

    # Determine message
    message = " ".join(args.message) if args.message else ""

    if args.interactive or not message:
        asyncio.run(interactive_mode(agent))
    else:
        # Single command mode with clean output
        try:
            asyncio.run(agent.run_async(message))
        except Exception as e:
            print(f"✗ Error: {e}")


def list_tools():
    """List all available Cogency tools."""
    print("\n🔧 Available Cogency Tools\n")
    print("Core Tools:")

    core_tools = [
        ("files", "📁", "Local filesystem I/O (create, read, edit, list)"),
        ("shell", "💻", "System command execution"),
        ("http", "🌐", "HTTP requests and API calls"),
        ("scrape", "📖", "Web content extraction"),
        ("search", "🔍", "Web search and information discovery"),
    ]

    for name, emoji, desc in core_tools:
        print(f"  {emoji} {name:<10} - {desc}")

    print(f"\nTotal: {len(core_tools)} core tools available")
    print("\nUsage: Agent('assistant', tools=['files', 'shell'])")
    print("Docs: https://github.com/teebee-ai/cogency/docs/tools.md")


def init_project(name: str):
    """Initialize a new Cogency project."""
    project_path = Path(name)

    if project_path.exists():
        print(f"Error: Directory '{name}' already exists")
        sys.exit(1)

    # Create project structure
    project_path.mkdir()

    # Create main.py
    main_py = """from cogency import Agent

# Create your agent (works out-of-box with Ollama)
agent = Agent(
    name="assistant",
    tools=["files", "shell"],
    identity="You are a helpful AI assistant."
)

# Production providers (requires extras):
# agent = Agent("assistant", llm="gemini")    # pip install cogency[gemini]
# agent = Agent("assistant", llm="anthropic") # pip install cogency[anthropic]

# Custom OpenAI-compatible endpoint:
# import os
# os.environ["OPENAI_BASE_URL"] = "http://localhost:11434/v1"  # Ollama
# os.environ["OPENAI_API_KEY"] = "ollama"

# Interactive mode
if __name__ == "__main__":
    import asyncio
    
    async def main():
        while True:
            query = input("\\n> ")
            if query.lower() in ["exit", "quit"]:
                break
            
            response = await agent.run_async(query)
            print(f"🤖 {response}")
    
    asyncio.run(main())
"""

    (project_path / "main.py").write_text(main_py)

    # Create pyproject.toml
    pyproject = f"""[project]
name = "{name}"
version = "0.1.0"
description = "A Cogency AI agent project"
dependencies = [
    "cogency",
]

[build-system]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"
"""

    (project_path / "pyproject.toml").write_text(pyproject)

    # Create README
    readme = f"""# {name}

A Cogency AI agent project.

## Setup

```bash
pip install cogency
```

## Run

```bash
python main.py
```

## Agent Configuration

Edit `main.py` to customize your agent:

- **Tools**: Add `"http"`, `"search"`, `"scrape"` for web capabilities
- **Identity**: Define your agent's personality and role
- **LLM**: Specify provider with `llm="gemini"` or `llm="openai"`

See [Cogency docs](https://github.com/teebee-ai/cogency) for more options.
"""

    (project_path / "README.md").write_text(readme)

    print(f"\n✅ Created Cogency project: {name}")
    print("\nNext steps:")
    print(f"  cd {name}")
    print("  pip install cogency")
    print("  python main.py")
    print("\n🚀 Happy building!")


if __name__ == "__main__":
    main()
