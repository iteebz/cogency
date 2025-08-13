"""Canonical agent and tool setup - single source of truth."""

import sys
from pathlib import Path


def setup_tools(tool_names_str: str, retrieval_path: str = None) -> list:
    """Setup tools from comma-separated string - canonical implementation."""
    from cogency.tools import Files, Recall, Scrape, Search, Shell

    tools = []
    tool_names = tool_names_str.split(",")

    for tool_name in tool_names:
        tool_name = tool_name.strip()
        if tool_name == "Files":
            tools.append(Files())
        elif tool_name == "Shell":
            tools.append(Shell())
        elif tool_name == "Search":
            tools.append(Search())
        elif tool_name == "Scrape":
            tools.append(Scrape())
        elif tool_name == "Recall":
            tools.append(Recall())
        elif tool_name == "Retrieve":
            import os

            retrieval_path = retrieval_path or os.getenv("COGENCY_RETRIEVAL_PATH")
            if retrieval_path:
                from cogency.tools import Retrieve

                embeddings_file = Path(retrieval_path).expanduser() / "embeddings.json"
                tools.append(Retrieve(embeddings_path=str(embeddings_file)))
            else:
                print("⚠️  Retrieve tool requires --retrieval-path or COGENCY_RETRIEVAL_PATH")
                sys.exit(1)
        else:
            print(f"✗ Unknown tool: {tool_name}")
            print("Available tools: Files, Shell, Search, Scrape, Recall, Retrieve")
            sys.exit(1)

    return tools


def setup_agent(tool_names: str, memory_enabled: bool, retrieval_path: str = None):
    """Setup agent with tools and memory - canonical implementation."""
    from cogency import Agent

    try:
        # Setup tools using canonical implementation
        tools = setup_tools(tool_names, retrieval_path)

        # Create agent with explicit memory setting
        return Agent("assistant", tools=tools, memory=memory_enabled)
    except Exception as e:
        print(f"✗ Failed to initialize agent: {e}")
        print("Check your API keys and configuration")
        sys.exit(1)
