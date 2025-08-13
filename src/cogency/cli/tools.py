"""Tool diagnostics and management."""

import inspect
import time
from pathlib import Path


async def tools_command(subcommand: str, tool_name: str = None):
    """Handle tool diagnostic commands."""
    from cogency.tools import Files, Recall, Retrieve, Scrape, Search, Shell

    # Setup tools for diagnostics
    tools = [Files(), Shell(), Search(), Scrape(), Recall()]

    # Add Retrieve if configured
    import os

    if retrieval_path := os.getenv("COGENCY_RETRIEVAL_PATH"):
        embeddings_file = Path(retrieval_path).expanduser() / "embeddings.json"
        tools.append(Retrieve(embeddings_path=str(embeddings_file)))

    if subcommand == "list":
        list_tools(tools)
    elif subcommand == "inspect":
        if not tool_name:
            print("Error: --tool-name required for inspect")
            return
        inspect_tool(tools, tool_name)
    elif subcommand == "test":
        await test_tools(tools, tool_name)
    elif subcommand == "benchmark":
        await benchmark_tools(tools)
    elif subcommand == "validate":
        validate_tools(tools)


def list_tools(tools):
    """List all available tools with descriptions."""
    print("🔧 Cogency Tool Registry")
    print("=" * 50)

    for tool in tools:
        emoji = getattr(tool, "emoji", "🔧")
        name = getattr(tool, "name", tool.__class__.__name__)
        description = getattr(tool, "description", "No description available")
        schema = getattr(tool, "schema", "No schema available")
        examples_count = len(getattr(tool, "examples", []))
        rules_count = len(getattr(tool, "rules", []))

        print(f"{emoji} {name.upper()}")
        print(f"   Description: {description}")
        print(f"   Schema: {schema}")
        print(f"   Examples: {examples_count} provided")
        print(f"   Rules: {rules_count} defined")
        print()


def inspect_tool(tools, tool_name: str):
    """Deep inspection of a specific tool."""
    tool = find_tool(tools, tool_name)
    if not tool:
        available = [getattr(t, "name", t.__class__.__name__) for t in tools]
        print(f"❌ Tool '{tool_name}' not found. Available: {available}")
        return

    emoji = getattr(tool, "emoji", "🔧")
    name = getattr(tool, "name", tool.__class__.__name__)

    print(f"🔍 Inspecting {emoji} {name.upper()}")
    print("=" * 50)

    print(f"Description: {getattr(tool, 'description', 'No description')}")
    print(f"Schema: {getattr(tool, 'schema', 'No schema')}")
    print(f"Emoji: {emoji}")

    examples = getattr(tool, "examples", [])
    if examples:
        print(f"\n📋 Examples ({len(examples)}):")
        for i, example in enumerate(examples, 1):
            print(f"  {i}. {example}")

    rules = getattr(tool, "rules", [])
    if rules:
        print(f"\n📜 Rules ({len(rules)}):")
        for i, rule in enumerate(rules, 1):
            print(f"  {i}. {rule}")

    # Show run method signature
    if hasattr(tool, "run"):
        print("\n🔧 Run Method Signature:")
        try:
            sig = inspect.signature(tool.run)
            print(f"  {sig}")
        except Exception as e:
            print(f"  Could not inspect signature: {e}")


async def test_tools(tools, tool_name: str = None):
    """Test tools with basic operations."""
    if tool_name:
        tool = find_tool(tools, tool_name)
        if not tool:
            available = [getattr(t, "name", t.__class__.__name__) for t in tools]
            print(f"❌ Tool '{tool_name}' not found. Available: {available}")
            return
        await test_single_tool(tool)
    else:
        print("🧪 Testing All Tools")
        print("=" * 50)
        for tool in tools:
            await test_single_tool(tool)
            print()


async def test_single_tool(tool):
    """Test a single tool with safe operations."""
    emoji = getattr(tool, "emoji", "🔧")
    name = getattr(tool, "name", tool.__class__.__name__)

    print(f"🧪 Testing {emoji} {name.upper()}")

    try:
        # Basic connectivity/initialization test
        if hasattr(tool, "run"):
            # Try a safe test based on tool type
            if "Files" in tool.__class__.__name__:
                # Test file listing in current directory
                result = await tool.run(action="list", path=".")
                status = "✅" if getattr(result, "success", True) else "❌"
                print(f"   {status} File listing test completed")
            elif "Shell" in tool.__class__.__name__:
                # Test safe echo command
                result = await tool.run(command="echo test")
                status = "✅" if getattr(result, "success", True) else "❌"
                print(f"   {status} Shell echo test completed")
            else:
                print("   ⚠️ No safe test available for this tool type")
        else:
            print("   ⚠️ Tool has no run method")
    except Exception as e:
        print(f"   ❌ Test failed: {e}")


async def benchmark_tools(tools):
    """Run performance benchmarks on tools."""
    print("⚡ Tool Performance Benchmarks")
    print("=" * 50)

    for tool in tools:
        name = getattr(tool, "name", tool.__class__.__name__)

        try:
            if hasattr(tool, "run"):
                times = []
                # Run 3 iterations for average
                for _ in range(3):
                    start = time.time()
                    # Safe benchmark operations
                    if "Files" in tool.__class__.__name__:
                        await tool.run(action="list", path=".")
                    elif "Shell" in tool.__class__.__name__:
                        await tool.run(command="echo benchmark")
                    else:
                        # Skip tools without safe benchmark operations
                        continue
                    times.append((time.time() - start) * 1000)

                if times:
                    avg_time = sum(times) / len(times)
                    print(f"   {name}: {avg_time:.1f}ms avg")
                else:
                    print(f"   {name}: no benchmark available")
            else:
                print(f"   {name}: no run method")
        except Exception as e:
            print(f"   {name}: benchmark failed - {e}")


def validate_tools(tools):
    """Validate tool schemas and required attributes."""
    print("✅ Tool Schema Validation")
    print("=" * 50)

    for tool in tools:
        name = getattr(tool, "name", tool.__class__.__name__)
        print(f"🔍 {name}:")

        # Check required attributes
        required_attrs = ["name", "description"]
        missing = [
            attr for attr in required_attrs if not hasattr(tool, attr) or not getattr(tool, attr)
        ]

        if missing:
            print(f"   ❌ Missing attributes: {missing}")
        else:
            print("   ✅ Basic attributes present")

        # Check for run method
        if hasattr(tool, "run"):
            print("   ✅ Has run method")
        else:
            print("   ❌ Missing run method")

        # Check examples
        examples = getattr(tool, "examples", [])
        if examples:
            print(f"   ✅ {len(examples)} examples defined")
        else:
            print("   ⚠️ No examples defined")


def find_tool(tools, name: str):
    """Find tool by name (case insensitive)."""
    name_lower = name.lower()
    for tool in tools:
        tool_name = getattr(tool, "name", tool.__class__.__name__).lower()
        if tool_name == name_lower or tool.__class__.__name__.lower() == name_lower:
            return tool
    return None
