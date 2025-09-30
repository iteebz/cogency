"""Evaluation runner - module interface + CLI."""

import asyncio
import json
import random
import sys
from datetime import datetime

from cogency.lib.paths import Paths

from .generate import coding, continuity, conversation, integrity, reasoning, research, security
from .runner import run_category


async def run(category=None, samples=2, llm="gemini", mode="replay", seed=42, concurrency=2):
    """Run evaluation category or full suite."""
    random.seed(seed)

    judge_llm = _judge_for(llm)
    agent_kwargs = {"llm": llm, "mode": mode, "concurrency": concurrency}

    if category:
        return await _run_single(category, samples, agent_kwargs, judge_llm, llm, mode, seed)
    return await _run_all(samples, agent_kwargs, judge_llm, llm, mode, seed)


async def _run_single(category, samples, agent_kwargs, judge_llm, llm, mode, seed):
    """Execute single category evaluation."""
    print(f"🧠 {category.capitalize()} Evaluation")
    print("=" * 40)

    generator = _generators()[category]
    cases = generator(samples)
    result = await run_category(category, cases, agent_kwargs, judge_llm)

    run_id = _persist_run([result], samples, llm, mode, judge_llm, seed)

    print(f"Results: {result.get('passed', 0)}/{result['total']}")
    print(f"Saved: {Paths.evals(f'runs/{run_id}')}")

    return result


async def _run_all(samples, agent_kwargs, judge_llm, llm, mode, seed):
    """Execute full evaluation suite."""
    print("🧠 Cogency Evaluation Suite v3.0.0")
    print("=" * 50)

    generators = _generators()

    results = await asyncio.gather(
        *[
            run_category(name, gen(samples), agent_kwargs, judge_llm)
            for name, gen in generators.items()
        ]
    )

    total = sum(r["total"] for r in results)
    passed = sum(r.get("passed", 0) for r in results if r.get("passed") is not None)
    rate = passed / total if total else 0

    run_id = _persist_run(results, samples, llm, mode, judge_llm, seed)

    print(f"Overall: {rate:.1%}")
    for result in results:
        rate = f"{result.get('rate', 0):.1%}" if result.get("rate") else "Raw"
        print(f"{result['category'].capitalize()}: {rate}")
    print(f"Latest: {Paths.evals(f'runs/{run_id}')}")

    return {
        "run_id": run_id,
        "version": "v3.0.1",
        "total": total,
        "passed": passed,
        "rate": f"{passed / total:.1%}" if total else "0.0%",
        "categories": {r["category"]: r for r in results},
    }


def _persist_run(results, samples, llm, mode, judge_llm, seed):
    """Persist run results to disk."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"{timestamp}_{llm}_{mode}"

    run_dir = Paths.evals(f"runs/{run_id}")
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
            "version": "v3.0.1",
            "total": total,
            "passed": passed,
            "rate": f"{passed / total:.1%}" if total else "0.0%",
            "categories": {r["category"]: r for r in results},
        }
        with open(run_dir / "summary.json", "w") as f:
            json.dump(summary, f, indent=2)

    latest_link = Paths.evals("latest")
    if latest_link.exists() or latest_link.is_symlink():
        latest_link.unlink()
    latest_link.symlink_to(f"runs/{run_id}")

    return run_id


def _generators():
    """Category generators."""
    return {
        "reasoning": reasoning,
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
    latest_link = Paths.evals("latest")
    if latest_link.exists():
        summary_file = latest_link / "summary.json"
        if summary_file.exists():
            with open(summary_file) as f:
                return json.load(f)
    return None


def logs(test_id):
    """Get debug logs for specific test."""
    return f"Debug logs for {test_id} - not yet implemented"


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

    category = args[0] if args else None
    await run(category, samples, llm, mode, seed, concurrency)


if __name__ == "__main__":
    asyncio.run(cli())
