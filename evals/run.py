"""CLI entry point for evals."""

from __future__ import annotations

import asyncio
import sys


def parse_args(args: list[str]) -> dict:
    """Parse CLI arguments."""
    parsed = {
        "command": "run",
        "tag": None,
        "cases": [],
        "judge": False,
        "concurrency": 2,
        "mechanical_only": False,
        "behavioral_only": False,
        "list_cases": False,
        "validate": False,
        "help": False,
    }

    i = 0
    while i < len(args):
        arg = args[i]

        if arg in ("run", "list", "validate"):
            parsed["command"] = arg
        elif arg == "--tag":
            i += 1
            parsed["tag"] = args[i] if i < len(args) else None
        elif arg == "--cases":
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                parsed["cases"].append(args[i])
                i += 1
            i -= 1
        elif arg == "--judge":
            parsed["judge"] = True
        elif arg == "--concurrency":
            i += 1
            parsed["concurrency"] = int(args[i]) if i < len(args) else 2
        elif arg == "--mechanical":
            parsed["mechanical_only"] = True
        elif arg == "--behavioral":
            parsed["behavioral_only"] = True
        elif arg == "--list":
            parsed["list_cases"] = True
        elif arg == "--validate":
            parsed["validate"] = True
        elif arg in ("-h", "--help"):
            parsed["help"] = True
        elif not arg.startswith("--"):
            parsed["cases"].append(arg)

        i += 1

    return parsed


def list_cases() -> None:
    """List all available cases."""
    from .cases import all_cases

    cases = all_cases()

    print(f"\nCogency Evals: {len(cases)} cases\n")
    print("=" * 60)

    tags: dict[str, list[str]] = {}
    for case in cases:
        for tag in case.tags:
            if tag not in tags:
                tags[tag] = []
            tags[tag].append(case.name)

    for tag in sorted(tags.keys()):
        print(f"\n[{tag}] ({len(tags[tag])} cases)")
        for name in sorted(tags[tag]):
            case = next(c for c in cases if c.name == name)
            judge_marker = " (judge)" if case.rubric else ""
            print(f"  {name}{judge_marker}")

    print("\n" + "=" * 60)
    print(f"Mechanical: {len([c for c in cases if not c.rubric])}")
    print(f"Behavioral: {len([c for c in cases if c.rubric])}")


async def run_evals(args: dict) -> int:
    """Run eval suite."""
    from .cases import all_cases, behavioral_cases, cases_by_tag, mechanical_cases
    from .harness import run_case, run_suite

    if args["cases"]:
        cases = [c for c in all_cases() if c.name in args["cases"]]
        missing = set(args["cases"]) - {c.name for c in cases}
        if missing:
            print(f"Cases not found: {', '.join(sorted(missing))}")
            return 1
    elif args["tag"]:
        cases = cases_by_tag(args["tag"])
        if not cases:
            print(f"No cases with tag: {args['tag']}")
            return 1
    elif args["mechanical_only"]:
        cases = mechanical_cases()
    elif args["behavioral_only"]:
        cases = behavioral_cases()
    else:
        cases = all_cases()

    print("\nCogency Evals")
    print("=" * 50)
    print(f"Cases: {len(cases)}")
    print(f"Judge: {'enabled' if args['judge'] else 'disabled'}")
    print(f"Concurrency: {args['concurrency']}")
    print("=" * 50 + "\n")

    if len(cases) == 1:
        verdict = await run_case(cases[0], judge=args["judge"])
        _print_verdict(verdict)
        return 0 if verdict.passed else 1

    summary = await run_suite(
        cases,
        concurrency=args["concurrency"],
        judge=args["judge"],
    )

    _print_summary(summary)

    return 0 if summary["failed"] == 0 else 1


def _print_verdict(verdict) -> None:
    """Print single verdict."""
    status = "✓ PASS" if verdict.passed else "✗ FAIL"
    print(f"\n{verdict.case}: {status}")

    if verdict.failures:
        print("\nFailures:")
        for f in verdict.failures:
            print(f"  [{f.mode}] {f.assertion}: {f.error}")
            if f.evidence:
                for k, v in f.evidence.items():
                    print(f"    {k}: {v}")

    if verdict.score:
        print(f"\nJudge: {'PASS' if verdict.score.passed else 'FAIL'}")
        print(f"  Confidence: {verdict.score.confidence}")
        for reason in verdict.score.reasons:
            print(f"  - {reason}")

    print(f"\nDuration: {verdict.duration:.2f}s")


def _print_summary(summary: dict) -> None:
    """Print suite summary."""
    print("\n" + "=" * 50)
    print(f"Results: {summary['passed']}/{summary['total']} ({summary['rate']})")
    print("=" * 50)

    failures = [v for v in summary["verdicts"] if not v["passed"]]
    if failures:
        print("\nFailed:")
        for v in failures:
            print(f"  ✗ {v['case']} ({v['failure_count']} failures)")

    passes = [v for v in summary["verdicts"] if v["passed"]]
    if passes and len(passes) <= 10:
        print("\nPassed:")
        for v in passes:
            print(f"  ✓ {v['case']}")

    print(f"\nArtifacts: .cogency/evals/runs/{summary['run_id']}")


def print_help() -> None:
    """Print help message."""
    print("""
Cogency Evals - Reference-grade test harness

Usage:
  python -m evals [command] [options]

Commands:
  run         Run eval cases (default)
  list        List all available cases
  validate    Validate case inventory

Options:
  --cases <names>    Run specific cases by name
  --tag <tag>        Run cases with specific tag
  --mechanical       Run only mechanical cases (no judge)
  --behavioral       Run only behavioral cases (with judge)
  --judge            Enable LLM judge (uses Claude CLI)
  --concurrency <n>  Parallel case execution (default: 2)
  --list             List all cases
  --validate         Validate case inventory
  -h, --help         Show this help

Examples:
  python -m evals --list
  python -m evals --cases write_creates_file recall_finds_past
  python -m evals --tag security --concurrency 4
  python -m evals --mechanical --concurrency 8
  python -m evals --behavioral --judge
""")


def validate() -> int:
    """Validate case inventory."""
    from .cases import EXPECTED_CASE_COUNT, all_cases, validate_cases

    print("\nValidating case inventory...")

    try:
        validate_cases()
        cases = all_cases()
        print(f"✓ Case count: {len(cases)} (expected {EXPECTED_CASE_COUNT})")
        print("✓ No duplicate names")
        print("✓ All required tags present")
        print("✓ All cases have assertions or rubrics")
        print("\nValidation: PASSED")
        return 0
    except AssertionError as e:
        print(f"✗ {e}")
        print("\nValidation: FAILED")
        return 1


def main() -> int:
    """CLI entry point."""
    args = parse_args(sys.argv[1:])

    if args["help"]:
        print_help()
        return 0

    if args["validate"] or args["command"] == "validate":
        return validate()

    if args["list_cases"] or args["command"] == "list":
        list_cases()
        return 0

    return asyncio.run(run_evals(args))


if __name__ == "__main__":
    sys.exit(main())
