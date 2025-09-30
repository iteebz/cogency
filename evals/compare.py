"""Run comparison tool - analyze performance between evaluation runs."""

import json
import sys

from cogency.lib.paths import Paths


def list_runs() -> list[str]:
    """List available evaluation runs."""
    runs_dir = Paths.evals("runs")
    if not runs_dir.exists():
        return []

    return sorted([d.name for d in runs_dir.iterdir() if d.is_dir()], reverse=True)


def load_run(run_id: str) -> dict:
    """Load run data including summary and config."""
    run_dir = Paths.evals(f"runs/{run_id}")

    if not run_dir.exists():
        raise ValueError(f"Run {run_id} not found")

    summary = {}
    config = {}

    summary_file = run_dir / "summary.json"
    if summary_file.exists():
        with open(summary_file) as f:
            summary = json.load(f)
    else:
        category_files = [f for f in run_dir.glob("*.json") if f.name != "config.json"]
        if category_files:
            with open(category_files[0]) as f:
                cat_data = json.load(f)
            summary = {
                "total": cat_data.get("total", 0),
                "passed": cat_data.get("passed", 0),
                "categories": {cat_data["category"]: cat_data},
            }

    config_file = run_dir / "config.json"
    if config_file.exists():
        with open(config_file) as f:
            config = json.load(f)

    return {"run_id": run_id, "summary": summary, "config": config}


def compare_runs(run1_id: str, run2_id: str) -> None:
    """Compare two evaluation runs."""
    try:
        run1 = load_run(run1_id)
        run2 = load_run(run2_id)
    except ValueError as e:
        print(f"❌ {e}")
        return

    print("📊 Comparing Runs")
    print(f"{'=' * 50}")
    print(f"Run A: {run1_id}")
    print(f"Run B: {run2_id}")
    print()

    _print_config(run1["config"], run2["config"])
    _print_performance(run1["summary"], run2["summary"])
    _print_efficiency(run1["summary"], run2["summary"])
    _print_categories(run1["summary"], run2["summary"])
    _print_verdict(run1["summary"], run2["summary"], run1_id, run2_id)


def _print_config(config1: dict, config2: dict):
    """Print configuration comparison."""
    print("🔧 Configuration")
    print(f"{'=' * 30}")
    print(f"{'LLM:':<15} {config1.get('llm', 'N/A'):<10} vs {config2.get('llm', 'N/A')}")
    print(f"{'Mode:':<15} {config1.get('mode', 'N/A'):<10} vs {config2.get('mode', 'N/A')}")
    print(
        f"{'Samples:':<15} {config1.get('sample_size', 'N/A'):<10} vs {config2.get('sample_size', 'N/A')}"
    )
    print(f"{'Judge:':<15} {config1.get('judge', 'N/A'):<10} vs {config2.get('judge', 'N/A')}")
    print(f"{'Seed:':<15} {config1.get('seed', 'random'):<10} vs {config2.get('seed', 'random')}")
    print()


def _print_performance(summary1: dict, summary2: dict):
    """Print performance comparison."""
    print("📈 Performance")
    print(f"{'=' * 30}")

    total1, total2 = summary1.get("total", 0), summary2.get("total", 0)
    passed1, passed2 = summary1.get("passed", 0), summary2.get("passed", 0)

    rate1 = passed1 / total1 if total1 else 0
    rate2 = passed2 / total2 if total2 else 0
    rate_diff = rate2 - rate1

    print(f"{'Total:':<15} {total1:<10} vs {total2}")
    print(f"{'Passed:':<15} {passed1:<10} vs {passed2}")
    print(f"{'Rate:':<15} {rate1:.1%}      vs {rate2:.1%}      ({rate_diff:+.1%})")
    print()


def _print_efficiency(summary1: dict, summary2: dict):
    """Print token and runtime efficiency comparison."""
    print("⚡ Efficiency")
    print(f"{'=' * 30}")

    categories1 = summary1.get("categories", {})
    categories2 = summary2.get("categories", {})

    tokens1 = sum(cat.get("tokens", {}).get("total", 0) for cat in categories1.values())
    tokens2 = sum(cat.get("tokens", {}).get("total", 0) for cat in categories2.values())

    runtime1 = sum(cat.get("runtime", {}).get("total", 0) for cat in categories1.values())
    runtime2 = sum(cat.get("runtime", {}).get("total", 0) for cat in categories2.values())

    token_diff = tokens2 - tokens1
    token_pct = (token_diff / tokens1 * 100) if tokens1 else 0

    runtime_diff = runtime2 - runtime1
    runtime_pct = (runtime_diff / runtime1 * 100) if runtime1 else 0

    print(f"{'Tokens:':<15} {tokens1:<10,} vs {tokens2:,} ({token_diff:+,} / {token_pct:+.1f}%)")
    print(
        f"{'Runtime:':<15} {runtime1:<10.1f}s vs {runtime2:.1f}s ({runtime_diff:+.1f}s / {runtime_pct:+.1f}%)"
    )
    print()


def _print_categories(summary1: dict, summary2: dict):
    """Print category breakdown."""
    print("📋 Categories")
    print(f"{'=' * 30}")

    categories1 = summary1.get("categories", {})
    categories2 = summary2.get("categories", {})

    all_categories = set(categories1.keys()) | set(categories2.keys())

    for category in sorted(all_categories):
        cat1 = categories1.get(category, {})
        cat2 = categories2.get(category, {})

        rate1 = cat1.get("rate", 0) if isinstance(cat1.get("rate"), (int, float)) else 0
        rate2 = cat2.get("rate", 0) if isinstance(cat2.get("rate"), (int, float)) else 0
        diff = rate2 - rate1

        tokens1 = cat1.get("tokens", {}).get("avg", 0)
        tokens2 = cat2.get("tokens", {}).get("avg", 0)

        symbol = "📈" if diff > 0.05 else "📉" if diff < -0.05 else "➡️"
        print(
            f"{symbol} {category:<12} {rate1:.1%} vs {rate2:.1%} ({diff:+.1%})  |  {tokens1:,} vs {tokens2:,} tok"
        )

    print()


def _print_verdict(summary1: dict, summary2: dict, run1_id: str, run2_id: str):
    """Print final verdict."""
    total1, total2 = summary1.get("total", 0), summary2.get("total", 0)
    passed1, passed2 = summary1.get("passed", 0), summary2.get("passed", 0)

    rate1 = passed1 / total1 if total1 else 0
    rate2 = passed2 / total2 if total2 else 0
    rate_diff = rate2 - rate1

    if rate_diff > 0.05:
        print(f"🏆 Run B ({run2_id}) wins by {rate_diff:.1%}")
    elif rate_diff < -0.05:
        print(f"🏆 Run A ({run1_id}) wins by {-rate_diff:.1%}")
    else:
        print("🤝 Runs are equivalent (< 5% difference)")


def main():
    """CLI entry point."""
    if len(sys.argv) < 3:
        print("Usage: python -m evals.compare <run1> <run2>")
        print("\nAvailable runs:")
        runs = list_runs()
        if not runs:
            print("  No runs found")
        else:
            for run in runs[:10]:
                print(f"  {run}")
        return

    run1_id = sys.argv[1]
    run2_id = sys.argv[2]

    compare_runs(run1_id, run2_id)


if __name__ == "__main__":
    main()
