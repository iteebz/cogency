#!/usr/bin/env python3
"""
VALIDATION FRAMEWORK
Common abstractions for test execution with standardized Agent runtime.
"""

import asyncio
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from cogency import Agent
from cogency.notify import EmojiFormatter


@dataclass
class ValidationConfig:
    """Standard validation configuration for all tests."""

    enable_trace: bool = True
    enable_metrics: bool = True
    timeout: int = 120
    memory: bool = False
    depth: int = 5
    formatter_class = EmojiFormatter


class BaseValidator:
    """Base class for all validation tests."""

    def __init__(self, name: str, description: str, config: Optional[ValidationConfig] = None):
        self.name = name
        self.description = description
        self.config = config or ValidationConfig()
        self.start_time = None
        self.results = []

    def create_agent(self, identity: str, tools: Optional[List] = None, **kwargs) -> Agent:
        """Create standardized agent with notify/trace."""
        agent_config = {
            "identity": identity,
            "memory": self.config.memory,
            "depth": self.config.depth,
            "formatter": self.config.formatter_class(),
            "observe": self.config.enable_metrics,
            "notify": True,
            **kwargs,
        }

        if tools:
            agent_config["tools"] = tools

        return Agent(f"{self.name.lower().replace(' ', '_')}_agent", **agent_config)

    def print_header(self):
        """Print test header."""
        print(f"\n{self.name.upper()}")
        print("=" * 60)
        print(f"{self.description}")
        print("=" * 60)

    def print_test(self, test_num: int, query: str):
        """Print individual test."""
        print(f"\nTest {test_num}: {query}")
        print("-" * 40)

    async def run_query(self, agent: Agent, query: str) -> str:
        """Execute query with streaming output."""
        result_parts = []

        async for chunk in agent.stream(query):
            if chunk.strip():
                print(chunk, end="", flush=True)

                # Collect non-notification chunks for result
                if not any(emoji in chunk for emoji in ["⚙️", "💭", "⚡", "🤖", "🔍", "🧠", "💾"]):
                    result_parts.append(chunk.strip())

        result = " ".join(result_parts).strip()
        print(f"\nResult: {result}")
        return result

    def validate_result(self, result: str, expected_patterns: List[str]) -> bool:
        """Validate result contains expected patterns."""
        for pattern in expected_patterns:
            if pattern.lower() not in result.lower():
                print(f"Missing pattern: '{pattern}'")
                return False
        print("All patterns validated")
        return True

    def print_summary(self, passed: int, total: int, duration: float):
        """Print test summary."""
        print(f"\n{'='*60}")
        print(f"{self.name} SUMMARY")
        print(f"{'='*60}")
        print(f"Duration: {duration:.1f}s")
        print(f"Tests: {passed}/{total} passed ({passed/total:.1%})")

        if passed == total:
            print("ALL TESTS PASSED")
        else:
            print(f"{total - passed} tests failed")

        print("=" * 60)

    async def run(self) -> bool:
        """Override this method in subclasses."""
        raise NotImplementedError("Subclasses must implement run()")


class ToolValidator(BaseValidator):
    """Specialized validator for tool testing."""

    def __init__(self, tool_name: str, tool_class, test_queries: List[str], **kwargs):
        super().__init__(
            f"{tool_name} Tool", f"Validation of {tool_name} tool functionality", **kwargs
        )
        self.tool_class = tool_class
        self.test_queries = test_queries

    async def run(self) -> bool:
        """Run tool validation tests."""
        self.print_header()
        self.start_time = time.time()

        # Create agent with the tool
        agent = self.create_agent(
            identity=f"expert {self.tool_class.__name__.lower()} user", tools=[self.tool_class()]
        )

        passed = 0
        total = len(self.test_queries)

        for i, query in enumerate(self.test_queries, 1):
            self.print_test(i, query)

            try:
                await asyncio.wait_for(self.run_query(agent, query), timeout=self.config.timeout)
                passed += 1
                print("✓ PASSED")

            except asyncio.TimeoutError:
                print(f"TIMEOUT after {self.config.timeout}s")
            except Exception as e:
                print(f"✗ FAILED: {e}")

            await asyncio.sleep(0.5)  # Brief pause

        duration = time.time() - self.start_time
        self.print_summary(passed, total, duration)

        return passed == total


class WorkflowValidator(BaseValidator):
    """Specialized validator for workflow testing."""

    def __init__(self, workflow_name: str, steps: List[Dict[str, Any]], **kwargs):
        super().__init__(
            f"{workflow_name} Workflow",
            f"Multi-step {workflow_name.lower()} workflow validation",
            **kwargs,
        )
        self.steps = steps

    async def run(self) -> bool:
        """Run workflow validation."""
        self.print_header()
        self.start_time = time.time()

        passed = 0
        total = len(self.steps)

        for i, step in enumerate(self.steps, 1):
            self.print_test(i, step["description"])

            # Create agent for this step
            agent = self.create_agent(
                identity=step.get("identity", "helpful assistant"), tools=step.get("tools", [])
            )

            try:
                result = await asyncio.wait_for(
                    self.run_query(agent, step["query"]),
                    timeout=step.get("timeout", self.config.timeout),
                )

                # Validate expected patterns if provided
                if "expected_patterns" in step:
                    if self.validate_result(result, step["expected_patterns"]):
                        passed += 1
                        print("✓ PASSED")
                    else:
                        print("✗ FAILED - Pattern validation failed")
                else:
                    passed += 1
                    print("✓ PASSED")

            except asyncio.TimeoutError:
                print(f"TIMEOUT after {step.get('timeout', self.config.timeout)}s")
            except Exception as e:
                print(f"✗ FAILED: {e}")

            await asyncio.sleep(1)  # Pause between workflow steps

        duration = time.time() - self.start_time
        self.print_summary(passed, total, duration)

        return passed == total


def create_standard_agent(name: str, **kwargs) -> Agent:
    """Create agent with standard validation configuration."""
    config = {
        "identity": f"validation agent for {name}",
        "memory": False,
        "depth": 5,
        "formatter": EmojiFormatter(),
        "observe": True,
        "notify": True,
        **kwargs,
    }
    return Agent(f"validator_{name.lower().replace(' ', '_')}", **config)


async def run_quick_validation(name: str, query: str, tools: Optional[List] = None) -> bool:
    """Quick validation helper for simple tests."""
    print(f"\n🎵 QUICK VALIDATION: {name}")
    print("=" * 40)

    agent = create_standard_agent(name, tools=tools or [])

    try:
        print(f"🧪 Query: {query}")
        print("-" * 40)

        start_time = time.time()
        async for chunk in agent.stream(query):
            print(chunk, end="", flush=True)

        duration = time.time() - start_time
        print(f"\n✓ Completed in {duration:.1f}s")
        return True

    except Exception as e:
        print(f"\n✗ Failed: {e}")
        return False


if __name__ == "__main__":
    # Example usage
    from cogency.tools import Calculator

    async def demo():
        validator = ToolValidator(
            "Calculator",
            Calculator,
            ["What is 25 * 4?", "Calculate the square root of 144", "What's 15% of 200?"],
        )
        success = await validator.run()
        return success

    success = asyncio.run(demo())
    sys.exit(0 if success else 1)
