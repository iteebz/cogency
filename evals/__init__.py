"""Cogency evals. Reference-grade test harness."""

from .cases import (
    EXPECTED_CASE_COUNT,
    Case,
    all_cases,
    behavioral_cases,
    cases_by_tag,
    mechanical_cases,
    validate_cases,
)
from .harness import Run, Verdict, execute, get_sandbox, run_case, run_suite
from .judge import Score, judge

__all__ = [
    "EXPECTED_CASE_COUNT",
    "Case",
    "Run",
    "Score",
    "Verdict",
    "all_cases",
    "behavioral_cases",
    "cases_by_tag",
    "execute",
    "get_sandbox",
    "judge",
    "mechanical_cases",
    "run_case",
    "run_suite",
    "validate_cases",
]
