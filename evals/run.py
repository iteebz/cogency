"""Baseline evaluation - canonical usage example."""

import asyncio
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from runner import run_baseline, run_category
from generators import security, continuity, reasoning, tooling


# Define categories - easily extensible
CATEGORIES = {
    "security": security,
    "tooling": tooling,
    "reasoning": reasoning,
    "continuity": continuity
}


async def main():
    """Run cognitive evaluation - single category or full baseline."""
    import sys
    
    # Check for single category argument
    if len(sys.argv) > 1:
        category_name = sys.argv[1].lower()
        if category_name in CATEGORIES:
            await run_category(category_name, CATEGORIES[category_name])
            return
        else:
            print(f"❌ Unknown category: {category_name}")
            print(f"Available: {', '.join(CATEGORIES.keys())}")
            return
    
    # Run full baseline
    print("🧠 Baseline Cognitive Evaluation v2.1.0")
    print("=" * 50)
    
    result = await run_baseline(CATEGORIES)
    
    print(f"\nResults saved to: {result['run_path']}")
    print(f"Overall: {result['summary']['overall_rate']}")
    for category, rate in result['summary']['breakdown'].items():
        print(f"{category.capitalize()}: {rate}")


if __name__ == "__main__":
    asyncio.run(main())