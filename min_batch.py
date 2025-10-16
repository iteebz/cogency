#!/usr/bin/env python3
"""Minimum viable cogency eval - 4 critical model/mode combinations."""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from evals.eval import run


async def main():
    """Run minimal batch across production bar."""

    # Production bar: 4 critical combos
    configs = [
        {"llm": "gemini", "mode": "resume", "name": "Gemini 2.5F + Live"},
        {"llm": "openai", "mode": "resume", "name": "GPT-4o Mini + Realtime"},
        {"llm": "gemini", "mode": "replay", "name": "Gemini 2.5F + HTTP"},
        {"llm": "openai", "mode": "replay", "name": "GPT-4o Mini + HTTP"},
    ]

    batch_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_dir = Path(f".cogency/batches/{batch_time}")
    batch_dir.mkdir(parents=True, exist_ok=True)

    print("\n🧬 MINIMUM VIABLE COGENCY EVAL")
    print(f"Batch: {batch_time}")
    print("=" * 60)

    results = {}

    for config in configs:
        llm = config["llm"]
        mode = config["mode"]
        name = config["name"]

        print(f"\n▶ {name}")
        print(f"  Config: {llm} ({mode})")

        try:
            result = await run(
                category=None,  # All categories
                samples=3,  # Mini: 3 per category
                llm=llm,
                mode=mode,
                seed=42,
                concurrency=2,
            )

            results[f"{llm}_{mode}"] = result

            # Also capture the run_id that was created
            latest_link = Path(".cogency/evals/latest")
            if latest_link.exists():
                run_id = latest_link.resolve().name
                results[f"{llm}_{mode}"]["run_id"] = run_id

        except Exception as e:
            print(f"  ✗ Error: {e}")
            results[f"{llm}_{mode}"] = {"error": str(e)}

    # Persist batch summary
    batch_summary = {
        "batch_id": batch_time,
        "timestamp": datetime.now().isoformat(),
        "configs": configs,
        "results": results,
    }

    with open(batch_dir / "summary.json", "w") as f:
        json.dump(batch_summary, f, indent=2)

    print("\n" + "=" * 60)
    print(f"📊 Batch complete: .cogency/batches/{batch_time}")
    print("   Results: .cogency/evals/runs/")

    # Print quick summary
    for config in configs:
        key = f"{config['llm']}_{config['mode']}"
        r = results.get(key, {})
        if "error" in r:
            print(f"   {config['name']}: ERROR")
        else:
            rate = r.get("rate", "?")
            print(f"   {config['name']}: {rate}")


if __name__ == "__main__":
    asyncio.run(main())
