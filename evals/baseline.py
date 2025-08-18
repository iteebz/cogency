"""Baseline evaluation - canonical usage example."""

import asyncio

from .runner import baseline_evaluation
from .generators import security, continuity, reasoning, tooling


# Define categories - easily extensible
CATEGORIES = {
    "security": security,
    "tooling": tooling,
    "reasoning": reasoning,
    "continuity": continuity
}


async def main():
    """Run baseline cognitive evaluation."""
    print("🧠 Baseline Cognitive Evaluation v2.1.0")
    print("=" * 50)
    
    result = await baseline_evaluation(CATEGORIES)
    
    print(f"\nResults saved to: {result['run_path']}")
    print(f"Overall: {result['summary']['overall_rate']}")
    for category, rate in result['summary']['breakdown'].items():
        print(f"{category.capitalize()}: {rate}")


if __name__ == "__main__":
    asyncio.run(main())