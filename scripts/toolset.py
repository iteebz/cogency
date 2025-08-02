#!/usr/bin/env python3
"""
Cogency Toolset Inspector

Purpose: Diagnostic utility for the canonical 5-tool architecture (Files, Shell, Search, Scrape, HTTP)
Scope: Tool validation, testing, and performance analysis during development
Created: Tool sharpening phase for v1.0.0 launch

Usage:
    python scripts/toolset.py list                    # List all available tools
    python scripts/toolset.py test                    # Test all tools with basic operations
    python scripts/toolset.py test <tool_name>        # Test specific tool
    python scripts/toolset.py inspect <tool_name>     # Inspect tool details
    python scripts/toolset.py benchmark               # Run performance benchmarks
    python scripts/toolset.py validate                # Validate tool schemas and examples
"""

import asyncio
import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cogency.tools import HTTP, Files, Scrape, Search, Shell
from cogency.tools.base import Tool


class ToolsetInspector:
    """Meta-agent utility for inspecting and testing the inner agent's tools."""

    def __init__(self):
        self.tools = {
            "files": Files("/tmp/cogency_toolset_test"),
            "search": Search(),
            "shell": Shell(),
            "scrape": Scrape(),
            "http": HTTP(),
        }

    def list_tools(self):
        """List all available tools with their descriptions."""
        print("🔧 Cogency Tool Registry")
        print("=" * 50)

        for _name, tool in self.tools.items():
            print(f"{tool.emoji} {tool.name.upper()}")
            print(f"   Description: {tool.description}")
            print(f"   Schema: {tool.schema}")
            print(f"   Examples: {len(tool.examples)} provided")
            print(f"   Rules: {len(tool.rules)} defined")
            print()

    def inspect_tool(self, tool_name: str):
        """Deep inspection of a specific tool."""
        if tool_name not in self.tools:
            print(f"❌ Tool '{tool_name}' not found. Available: {list(self.tools.keys())}")
            return

        tool = self.tools[tool_name]
        print(f"🔍 Inspecting {tool.emoji} {tool.name.upper()}")
        print("=" * 50)

        print(f"Description: {tool.description}")
        print(f"Schema: {tool.schema}")
        print(f"Emoji: {tool.emoji}")

        print(f"\n📋 Examples ({len(tool.examples)}):")
        for i, example in enumerate(tool.examples, 1):
            print(f"  {i}. {example}")

        print(f"\n📜 Rules ({len(tool.rules)}):")
        for i, rule in enumerate(tool.rules, 1):
            print(f"  {i}. {rule}")

        # Show parameter structure
        if hasattr(tool, "params"):
            print("\n🔧 Parameters:")
            import inspect

            sig = inspect.signature(tool.params)
            for param_name, param in sig.parameters.items():
                annotation = (
                    param.annotation if param.annotation != inspect.Parameter.empty else "Any"
                )
                default = f" = {param.default}" if param.default != inspect.Parameter.empty else ""
                print(f"  {param_name}: {annotation}{default}")

    async def test_tool(self, tool_name: str = None):
        """Test specific tool or all tools with basic operations."""
        if tool_name:
            if tool_name not in self.tools:
                print(f"❌ Tool '{tool_name}' not found. Available: {list(self.tools.keys())}")
                return
            await self._test_single_tool(tool_name, self.tools[tool_name])
        else:
            print("🧪 Testing All Tools")
            print("=" * 50)
            for name, tool in self.tools.items():
                await self._test_single_tool(name, tool)
                print()

    async def _test_single_tool(self, name: str, tool: Tool):
        """Test a single tool with appropriate test cases."""
        print(f"🧪 Testing {tool.emoji} {name.upper()}")

        try:
            if name == "files":
                await self._test_files(tool)
            elif name == "search":
                await self._test_search(tool)
            elif name == "shell":
                await self._test_shell(tool)
            elif name == "scrape":
                await self._test_scrape(tool)
            elif name == "http":
                await self._test_http(tool)
        except Exception as e:
            print(f"   ❌ CRITICAL ERROR: {e}")

    async def _test_files(self, tool: Files):
        """Test Files tool operations."""
        tests = [
            ("list", {"action": "list", "path": "."}),
            (
                "create",
                {
                    "action": "create",
                    "path": "test_meta.py",
                    "content": "# Meta-agent test file\nprint('Hello from meta-agent!')",
                },
            ),
            ("read", {"action": "read", "path": "test_meta.py"}),
            (
                "edit",
                {
                    "action": "edit",
                    "path": "test_meta.py",
                    "line": 2,
                    "content": "print('Updated by meta-agent!')",
                },
            ),
        ]

        for test_name, params in tests:
            result = await tool.run(**params)
            status = "✅" if result.success else "❌"
            details = (
                f"items: {len(result.data.get('items', []))}"
                if test_name == "list" and result.success
                else f"size: {result.data.get('size', 0)}"
                if result.success and "size" in result.data
                else result.error
                if not result.success
                else "success"
            )
            print(f"   {status} {test_name}: {details}")

    async def _test_search(self, tool: Search):
        """Test Search tool."""
        result = await tool.run(query="Python async programming", max_results=2)
        status = "✅" if result.success else "❌"
        details = (
            f"results: {len(result.data.get('results', []))}" if result.success else result.error
        )
        print(f"   {status} search: {details}")

    async def _test_shell(self, tool: Shell):
        """Test Shell tool."""
        tests = [
            ("safe_command", {"command": "echo 'meta-agent test'"}),
            ("blocked_command", {"command": "rm -rf /"}),
            ("python_version", {"command": "python --version"}),
        ]

        for test_name, params in tests:
            result = await tool.run(**params)
            if test_name == "blocked_command":
                status = "✅" if not result.success else "❌"
                details = (
                    "correctly blocked"
                    if not result.success
                    else "SECURITY ISSUE: should be blocked"
                )
            else:
                status = "✅" if result.success else "❌"
                details = (
                    result.data.get("stdout", "").strip()[:50] if result.success else result.error
                )
            print(f"   {status} {test_name}: {details}")

    async def _test_scrape(self, tool: Scrape):
        """Test Scrape tool."""
        result = await tool.run(url="https://example.com")
        status = "✅" if result.success else "⚠️"
        details = (
            f"content: {len(result.data.get('content', ''))} chars"
            if result.success
            else f"expected failure: {result.error}"
        )
        print(f"   {status} scrape: {details}")

    async def _test_http(self, tool: HTTP):
        """Test HTTP tool."""
        tests = [
            ("get", {"url": "https://httpbin.org/get", "method": "get"}),
            (
                "post",
                {
                    "url": "https://httpbin.org/post",
                    "method": "post",
                    "json_data": {"test": "meta-agent"},
                },
            ),
        ]

        for test_name, params in tests:
            result = await tool.run(**params)
            status = "✅" if result.success else "❌"
            details = (
                f"status: {result.data.get('status_code')}" if result.success else result.error
            )
            print(f"   {status} {test_name}: {details}")

    async def benchmark_tools(self):
        """Run performance benchmarks on tools."""
        print("⚡ Tool Performance Benchmarks")
        print("=" * 50)

        benchmarks = [
            ("files_list", lambda: self.tools["files"].run(action="list", path=".")),
            ("shell_echo", lambda: self.tools["shell"].run(command="echo benchmark")),
            ("http_get", lambda: self.tools["http"].run(url="https://httpbin.org/get")),
        ]

        for name, func in benchmarks:
            times = []
            for _ in range(3):
                start = time.time()
                result = await func()
                end = time.time()
                if result.success:
                    times.append((end - start) * 1000)

            if times:
                avg_time = sum(times) / len(times)
                print(f"   {name}: {avg_time:.1f}ms avg")
            else:
                print(f"   {name}: failed")

    def validate_schemas(self):
        """Validate tool schemas and examples."""
        print("✅ Schema Validation")
        print("=" * 50)

        for name, tool in self.tools.items():
            print(f"🔍 {name}:")

            # Check required attributes
            required_attrs = ["name", "description", "schema", "examples", "rules"]
            missing = [
                attr
                for attr in required_attrs
                if not hasattr(tool, attr) or not getattr(tool, attr)
            ]

            if missing:
                print(f"   ❌ Missing attributes: {missing}")
            else:
                print("   ✅ All required attributes present")

            # Check examples format
            if hasattr(tool, "examples") and tool.examples:
                valid_examples = all(
                    isinstance(ex, str) and tool.name + "(" in ex for ex in tool.examples
                )
                print(f"   {'✅' if valid_examples else '❌'} Examples format valid")

            # Check rules
            if hasattr(tool, "rules") and tool.rules:
                print(f"   ✅ {len(tool.rules)} rules defined")


async def main():
    """Main CLI interface."""
    inspector = ToolsetInspector()

    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1]

    if command == "list":
        inspector.list_tools()

    elif command == "test":
        tool_name = sys.argv[2] if len(sys.argv) > 2 else None
        await inspector.test_tool(tool_name)

    elif command == "inspect":
        if len(sys.argv) < 3:
            print("Usage: python toolset.py inspect <tool_name>")
            return
        inspector.inspect_tool(sys.argv[2])

    elif command == "benchmark":
        await inspector.benchmark_tools()

    elif command == "validate":
        inspector.validate_schemas()

    else:
        print(f"Unknown command: {command}")
        print(__doc__)


if __name__ == "__main__":
    asyncio.run(main())
