"""Evaluation runner - module interface + CLI."""

import asyncio
import json
import random
import sys
from datetime import datetime
from pathlib import Path

from cogency import __version__

from .generate import coding, continuity, conversation, integrity, research, security
from .runner import run_category


async def run(
    category=None, samples=2, llm="gemini", mode="replay", seed=42, concurrency=2, judge=True
):
    """Run evaluation category or full suite."""
    random.seed(seed)

    judge_llm = _judge_for(llm) if judge else None
    agent_kwargs = {"llm": llm, "mode": mode, "concurrency": concurrency}

    if category:
        return await _run_single(category, samples, agent_kwargs, judge_llm, llm, mode, seed)
    return await _run_all(samples, agent_kwargs, judge_llm, llm, mode, seed)


async def _run_single(category, samples, agent_kwargs, judge_llm, llm, mode, seed):
    """Execute single category evaluation."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"{timestamp}_{llm}_{mode}"

    print(f"🧠 {category.capitalize()} Evaluation")
    print("=" * 40)

    generator = _generators()[category]
    cases = generator(samples)
    result = await run_category(category, cases, agent_kwargs, judge_llm, run_id)

    _persist_run([result], samples, llm, mode, judge_llm, seed, run_id)

    if judge_llm:
        print(f"Results: {result.get('passed', 0)}/{result['total']}")
    else:
        avg_tokens = result.get("tokens", {}).get("avg", 0)
        print(f"Completed: {result['total']} tests, {avg_tokens:,} avg tokens")
    print(f"Saved: .cogency/evals/runs/{run_id}")

    return result


async def _run_all(samples, agent_kwargs, judge_llm, llm, mode, seed):
    """Execute full evaluation suite."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"{timestamp}_{llm}_{mode}"

    print(f"🧠 Cogency Evaluation Suite {__version__}")
    print("=" * 50)

    generators = _generators()

    results = await asyncio.gather(
        *[
            run_category(name, gen(samples), agent_kwargs, judge_llm, run_id)
            for name, gen in generators.items()
        ]
    )

    total = sum(r["total"] for r in results)
    passed = sum(r.get("passed", 0) for r in results if r.get("passed") is not None)
    rate = passed / total if total else 0

    _persist_run(results, samples, llm, mode, judge_llm, seed, run_id)

    if judge_llm:
        print(f"Overall: {rate:.1%}")
        for result in results:
            rate = f"{result.get('rate', 0):.1%}"
            print(f"{result['category'].capitalize()}: {rate}")
    else:
        print(f"Completed: {total} tests (no judge, manual review required)")
        for result in results:
            avg_tokens = result.get("tokens", {}).get("avg", 0)
            print(f"{result['category'].capitalize()}: {avg_tokens:,} avg tokens")
    print(f"Latest: .cogency/evals/runs/{run_id}")

    return {
        "run_id": run_id,
        "version": __version__,
        "total": total,
        "passed": passed,
        "rate": f"{passed / total:.1%}" if total else "0.0%",
        "categories": {r["category"]: r for r in results},
    }


def _persist_run(results, samples, llm, mode, judge_llm, seed, run_id):
    """Persist run results to disk."""

    run_dir = Path(f".cogency/evals/runs/{run_id}")
    run_dir.mkdir(parents=True, exist_ok=True)

    from cogency import Agent

    config_data = {
        "llm": Agent(llm=llm).config.llm.http_model,
        "mode": mode,
        "sample_size": samples,
        "judge": judge_llm.__class__.__name__ if judge_llm else None,
        "seed": seed,
        "timestamp": datetime.now().isoformat(),
    }

    with open(run_dir / "config.json", "w") as f:
        json.dump(config_data, f, indent=2)

    for result in results:
        with open(run_dir / f"{result['category']}.json", "w") as f:
            json.dump(result, f, indent=2)

    if len(results) > 1:
        total = sum(r["total"] for r in results)
        passed = sum(r.get("passed", 0) for r in results)
        summary = {
            "run_id": run_id,
            "version": __version__,
            "total": total,
            "passed": passed,
            "rate": f"{passed / total:.1%}" if total else "0.0%",
            "categories": {r["category"]: r for r in results},
        }
        with open(run_dir / "summary.json", "w") as f:
            json.dump(summary, f, indent=2)

    latest_link = Path(".cogency/evals/latest")
    if latest_link.exists() or latest_link.is_symlink():
        latest_link.unlink()
    latest_link.symlink_to(f"runs/{run_id}")

    return run_id


def _generators():
    """Category generators."""
    return {
        "conversation": conversation,
        "continuity": continuity,
        "coding": coding,
        "research": research,
        "security": security,
        "integrity": integrity,
    }


def _judge_for(llm: str):
    """Get cross-model judge."""
    from cogency.lib.llms import Gemini, OpenAI

    judges = {
        "gemini": OpenAI,
        "openai": Gemini,
        "anthropic": Gemini,
    }

    return judges.get(llm, Gemini)()


def latest():
    """Get latest evaluation summary."""
    latest_link = Path(".cogency/evals/latest")
    if latest_link.exists():
        summary_file = latest_link / "summary.json"
        if summary_file.exists():
            with open(summary_file) as f:
                return json.load(f)
    return None


def logs(run_id, test_id=None):
    """Get debug logs for specific run."""
    import sqlite3

    store_path = Path(f".cogency/evals/runs/{run_id}/store.db")
    if not store_path.exists():
        return None

    try:
        conn = sqlite3.connect(store_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM messages ORDER BY timestamp")
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        conn.close()

        return {
            "run_id": run_id,
            "store_db": str(store_path.relative_to(Path.cwd())),
            "columns": columns,
            "messages": [dict(zip(columns, row, strict=False)) for row in rows],
        }
    except Exception as e:
        return {"run_id": run_id, "error": str(e)}


async def cli():
    """CLI entry point."""

    def parse_arg(args, flag, default, cast=str):
        if flag in args:
            idx = args.index(flag)
            val = cast(args[idx + 1])
            del args[idx : idx + 2]
            return val
        return default

    args = sys.argv[1:]
    samples = parse_arg(args, "--samples", 2, int)
    seed = parse_arg(args, "--seed", 42, int)
    mode = parse_arg(args, "--mode", "replay")
    concurrency = parse_arg(args, "--concurrency", 2, int)
    llm = parse_arg(args, "--llm", "gemini")
    judge = "--judge" in sys.argv[1:]

    category = args[0] if args and not args[0].startswith("--") else None
    await run(category, samples, llm, mode, seed, concurrency, judge)


if __name__ == "__main__":
    asyncio.run(cli())
