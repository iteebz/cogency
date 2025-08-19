"""Baseline evaluation - canonical usage example."""

import asyncio
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from generators import continuity, reasoning, security, tooling
from runner import run_baseline, run_category

# Define categories - easily extensible
CATEGORIES = {
    "security": security,
    "tooling": tooling,
    "reasoning": reasoning,
    "continuity": continuity,
}


async def main():
    """Run cognitive evaluation - single category or full baseline."""
    import sys

    from config import CONFIG

    # Parse command line arguments
    args = sys.argv[1:]
    category_name = None

    # Handle --samples argument
    i = 0
    while i < len(args):
        if args[i] == "--samples" and i + 1 < len(args):
            try:
                CONFIG.sample_size = int(args[i + 1])
                print(f"📊 Sample size set to {CONFIG.sample_size}")
                args = args[:i] + args[i + 2 :]  # Remove processed args
            except ValueError:
                print(f"❌ Invalid sample size: {args[i + 1]}")
                return
        else:
            i += 1

    # Check for category argument
    if args:
        category_name = args[0].lower()
        if category_name in CATEGORIES:
            await run_category(category_name, CATEGORIES[category_name])
            return
        print(f"❌ Unknown category: {category_name}")
        print(f"Available: {', '.join(CATEGORIES.keys())}")
        return

    # Run full baseline
    print("🧠 Baseline Cognitive Evaluation v2.1.0")
    print("=" * 50)

    result = await run_baseline(CATEGORIES)

    print(f"\nResults saved to: {result['run_path']}")
    print(f"Overall: {result['summary']['overall_rate']}")
    for category, rate in result["summary"]["breakdown"].items():
        print(f"{category.capitalize()}: {rate}")


if __name__ == "__main__":
    asyncio.run(main())
