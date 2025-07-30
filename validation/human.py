#!/usr/bin/env python3
"""COGENCY VALIDATION SUITE"""

import asyncio
import subprocess
import sys
from pathlib import Path


async def run_test(script_path: Path, name: str, timeout: int = 120) -> bool:
    """Execute validation test with clean output."""
    print(f"\n{name}")
    print("=" * 60)

    try:
        result = subprocess.run(
            ["poetry", "run", "python", str(script_path)],
            cwd=script_path.parent.parent,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        # Show clean output
        if result.stdout:
            print(result.stdout)
        if result.stderr and "warning" not in result.stderr.lower():
            print(f"ERROR: {result.stderr}")

        success = result.returncode == 0
        print(f"{'✓ PASSED' if success else '✗ FAILED'}")
        return success

    except subprocess.TimeoutExpired:
        print(f"TIMEOUT ({timeout}s)")
        return False
    except Exception as e:
        print(f"CRASHED: {e}")
        return False


async def main():
    """Run all validation tests."""
    print("COGENCY VALIDATION SUITE")
    print("=" * 60)

    validation_dir = Path(__file__).parent

    # Core validation tests
    tests = [
        # Tools
        (validation_dir / "tools" / "calculator.py", "Calculator"),
        (validation_dir / "tools" / "code.py", "Code Execution"),
        (validation_dir / "tools" / "files.py", "File Operations"),
        (validation_dir / "tools" / "weather.py", "Weather API"),
        # Services
        (validation_dir / "services" / "llm.py", "LLM Providers"),
        (validation_dir / "services" / "embed.py", "Embedding Providers"),
        # Memory & State
        (validation_dir / "memory" / "search.py", "Memory Search"),
        (validation_dir / "state" / "persist.py", "State Persistence"),
        # Workflows
        (validation_dir / "workflows" / "math.py", "Math Workflow"),
        (validation_dir / "workflows" / "research.py", "Research Workflow"),
        # Notifications
        (validation_dir / "notify" / "trace.py", "Trace Output"),
        (validation_dir / "notify" / "silent.py", "Silent Mode"),
        # Robustness
        (validation_dir / "robust" / "failures.py", "Error Handling"),
        (validation_dir / "robust" / "recovery.py", "Error Recovery"),
    ]

    results = []
    for script_path, name in tests:
        if script_path.exists():
            success = await run_test(script_path, name)
            results.append((name, success))
            await asyncio.sleep(1)
        else:
            print(f"SKIP {name} - file not found")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION RESULTS")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✓" if success else "✗"
        print(f"{status} {name}")

    print("-" * 60)
    print(f"PASSED: {passed}/{total} ({passed/total:.1%})")

    if passed == total:
        print("All tests passed - ready for production")
    elif passed >= total * 0.8:
        print("Most tests passed - minor issues to resolve")
    else:
        print("Multiple failures - needs attention")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
