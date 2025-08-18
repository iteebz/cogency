"""Security-focused evaluation - post implementation validation."""

import asyncio
import sys
from pathlib import Path

# Add parent to path for relative imports
sys.path.append(str(Path(__file__).parent))

from core import evaluate_category
from generators import security
from storage import save_run


async def main():
    """Run security evaluation to validate semantic security implementation."""
    print("🛡️  Security Evaluation - Post Implementation")
    print("=" * 50)
    
    result = await evaluate_category("security", security)
    
    # Save individual result
    run_data = {
        "timestamp": result["results"][0]["timestamp"],
        "categories": {"security": result},
        "summary": {
            "overall_rate": f"{result['rate']:.1%}" if result['rate'] else "0%",
            "breakdown": {"security": f"{result['rate']:.1%}" if result['rate'] else "0%"}
        }
    }
    
    run_path = await save_run(run_data)
    
    print(f"\nSecurity Results:")
    print(f"Passed: {result['passed']}/{result['total']}")
    print(f"Rate: {result['rate']:.1%}" if result['rate'] else "Rate: 0%")
    print(f"Results saved to: {run_path}")
    
    # Show individual results for analysis
    print(f"\nDetailed Results:")
    for r in result['results']:
        status = "✅ PASS" if r.get('passed') else "❌ FAIL" 
        print(f"{r['test_id']}: {status}")
        print(f"  Prompt: {r['prompt'][:50]}...")
        print(f"  Response: {r['response'][:50]}...")


if __name__ == "__main__":
    asyncio.run(main())