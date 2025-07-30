#!/usr/bin/env python3
"""
VALIDATION UTILITIES
DRY utilities for common validation patterns.
"""

import asyncio
import time
from typing import List, Optional

from cogency import Agent
from cogency.notify import EmojiFormatter


def create_validator_agent(name: str, tools: Optional[List] = None, **kwargs) -> Agent:
    """Create standardized validation agent."""
    config = {
        "identity": f"validation agent for {name}",
        "memory": False,
        "depth": 5,
        "formatter": EmojiFormatter(),
        "observe": True,
        "notify": True,
        "trace": True,
        **kwargs,
    }

    if tools:
        config["tools"] = tools

    return Agent(f"validator_{name.lower().replace(' ', '_')}", **config)


def print_header(name: str, description: str):
    """Print validation header."""
    print(f"\n{name.upper()}")
    print("=" * 60)
    print(f"{description}")
    print("=" * 60)


def print_test(test_num: int, query: str):
    """Print individual test."""
    print(f"\nTest {test_num}: {query}")
    print("-" * 40)


async def run_query(agent: Agent, query: str) -> str:
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


def validate_patterns(result: str, expected_patterns: List[str]) -> bool:
    """Validate result contains expected patterns."""
    for pattern in expected_patterns:
        if pattern.lower() not in result.lower():
            print(f"Missing pattern: '{pattern}'")
            return False
    print("All patterns validated")
    return True


def print_summary(name: str, passed: int, total: int, duration: float):
    """Print validation summary."""
    print(f"\n{'='*60}")
    print(f"{name} SUMMARY")
    print(f"{'='*60}")
    print(f"Duration: {duration:.1f}s")
    print(f"Tests: {passed}/{total} passed ({passed/total:.1%})")

    if passed == total:
        print("ALL TESTS PASSED")
    else:
        print(f"{total - passed} tests failed")

    print("=" * 60)


async def quick_validation(name: str, query: str, tools: Optional[List] = None) -> bool:
    """Quick validation helper for simple tests."""
    print_header(name, f"Quick validation of {name.lower()}")

    agent = create_validator_agent(name, tools=tools)

    try:
        start_time = time.time()
        await run_query(agent, query)
        duration = time.time() - start_time

        print(f"\n✓ Completed in {duration:.1f}s")
        return True

    except Exception as e:
        print(f"\n✗ Failed: {e}")
        return False


async def multi_test_validation(
    name: str, description: str, tests: List[tuple], tools: Optional[List] = None
) -> bool:
    """Run multiple validation tests."""
    print_header(name, description)

    agent = create_validator_agent(name, tools=tools)
    start_time = time.time()

    passed = 0
    total = len(tests)

    for i, (query, expected_patterns) in enumerate(tests, 1):
        print_test(i, query)

        try:
            result = await asyncio.wait_for(run_query(agent, query), timeout=120)

            # Validate patterns if provided
            if expected_patterns and not validate_patterns(result, expected_patterns):
                print("✗ FAILED - Pattern validation failed")
            else:
                passed += 1
                print("✓ PASSED")

        except asyncio.TimeoutError:
            print("TIMEOUT")
        except Exception as e:
            print(f"✗ FAILED: {e}")

        await asyncio.sleep(0.5)

    duration = time.time() - start_time
    print_summary(name, passed, total, duration)

    return passed == total
