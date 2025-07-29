#!/usr/bin/env python3
"""Run all verification examples to test Cogency is singing 🎵"""

import asyncio
import subprocess
import sys
from pathlib import Path


async def run_example(script_path: Path, name: str) -> bool:
    """Run a single verification example."""
    print(f"\n🎵 Running {name}...")
    print("=" * 50)

    try:
        # Use poetry run to ensure proper environment
        result = subprocess.run(
            ["poetry", "run", "python", str(script_path)],
            cwd=script_path.parent.parent.parent,  # Back to cogency root
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout per test
        )

        print(result.stdout)
        if result.stderr:
            print(f"STDERR: {result.stderr}")

        if result.returncode == 0:
            print(f"✅ {name} PASSED")
            return True
        else:
            print(f"❌ {name} FAILED (exit code: {result.returncode})")
            return False

    except subprocess.TimeoutExpired:
        print(f"⏰ {name} TIMED OUT")
        return False
    except Exception as e:
        print(f"💥 {name} CRASHED: {e}")
        return False


async def main():
    """Run all verification tests."""
    print("🎵 COGENCY VERIFICATION SUITE 🎵")
    print("Testing if Cogency is singing her beautiful song...")
    print("=" * 60)

    verification_dir = Path(__file__).parent

    # Define test suite in order of complexity
    test_suite = [
        # Basic tool tests (quick wins)
        (verification_dir / "basic" / "calculator_test.py", "Calculator Tool"),
        (verification_dir / "basic" / "code_test.py", "Code Execution Tool"),
        (verification_dir / "basic" / "files_test.py", "File Operations Tool"),
        # (verification_dir / "basic" / "weather_test.py", "Weather Tool"),  # Commented out - API dependent
        # Tracing comparison
        (verification_dir / "tracing" / "silent_mode.py", "Silent Mode"),
        (verification_dir / "tracing" / "with_trace.py", "Tracing Mode"),
        # Complex workflows
        (verification_dir / "workflows" / "math_verify.py", "Math Verification Workflow"),
        (verification_dir / "workflows" / "data_flow.py", "Data Processing Workflow"),
        # (verification_dir / "workflows" / "research_code.py", "Research + Code Workflow"),  # Search dependent
        # Error handling
        (verification_dir / "errors" / "tool_failures.py", "Error Handling"),
        (verification_dir / "errors" / "recovery_tests.py", "Error Recovery"),
    ]

    results = []

    for script_path, test_name in test_suite:
        if script_path.exists():
            success = await run_example(script_path, test_name)
            results.append((test_name, success))
            await asyncio.sleep(2)  # Brief pause between tests
        else:
            print(f"⚠️ Skipping {test_name} - file not found: {script_path}")
            results.append((test_name, False))

    # Final results
    print("\n" + "=" * 60)
    print("🎵 VERIFICATION RESULTS 🎵")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status:8} {test_name}")

    print("-" * 60)
    print(f"SUMMARY: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎵 COGENCY IS SINGING HER BEAUTIFUL SONG! 🎵")
        print("All verification tests passed - the architecture is clean and working!")
    elif passed >= total * 0.8:  # 80% pass rate
        print("\n🎶 COGENCY IS MOSTLY SINGING! 🎶")
        print("Most tests passed - minor issues to investigate.")
    else:
        print("\n😞 COGENCY NEEDS TUNING...")
        print("Multiple test failures - architecture needs attention.")

    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
