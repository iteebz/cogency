import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class CheckResult:
    ok: bool
    score: int
    detail: str


def _check_ci() -> CheckResult:
    just_bin = shutil.which("just")
    if not just_bin:
        return CheckResult(ok=False, score=0, detail="just not found")
    result = subprocess.run(
        [just_bin, "ci"],
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    if result.returncode != 0:
        return CheckResult(ok=False, score=0, detail=f"CI failed: {result.returncode}")
    return CheckResult(ok=True, score=100, detail="CI passed")


def _check_build() -> CheckResult:
    dist_dir = Path("dist")
    if not dist_dir.exists():
        return CheckResult(ok=False, score=0, detail="dist/ missing")

    wheel = list(dist_dir.glob("*.whl"))
    tarball = list(dist_dir.glob("*.tar.gz"))

    if not wheel or not tarball:
        return CheckResult(ok=False, score=50, detail="incomplete build artifacts")

    return CheckResult(ok=True, score=100, detail="build artifacts valid")


def _check_docs() -> CheckResult:
    docs_dir = Path("docs")
    if not docs_dir.exists():
        return CheckResult(ok=False, score=0, detail="docs/ missing")

    md_files = list(docs_dir.glob("*.md"))
    if not md_files:
        return CheckResult(ok=False, score=0, detail="no doc files")

    return CheckResult(ok=True, score=100, detail=f"{len(md_files)} docs")


_CHECKS: list[tuple[str, Callable[[], CheckResult], int]] = [
    ("ci", _check_ci, 50),
    ("build", _check_build, 30),
    ("docs", _check_docs, 20),
]


def score() -> dict[str, Any]:
    results: dict[str, CheckResult] = {}
    total_weight = sum(w for _, _, w in _CHECKS)
    weighted_score = 0

    for name, check_fn, weight in _CHECKS:
        result = check_fn()
        results[name] = result
        weighted_score += (result.score / 100) * weight

    final_score = int((weighted_score / total_weight) * 100)
    all_ok = all(r.ok for r in results.values())

    return {
        "ok": all_ok,
        "score": final_score,
        "checks": {name: {"ok": r.ok, "detail": r.detail} for name, r in results.items()},
    }


def cli() -> None:
    result = score()
    print(f"health: {result['score']}/100 {'✓' if result['ok'] else '✗'}")
    for name, check in result["checks"].items():
        status = "✓" if check["ok"] else "✗"
        print(f"  {name}: {status} {check['detail']}")
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    cli()
