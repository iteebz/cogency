"""Evaluation framework for agent performance testing.

This module provides a comprehensive evaluation system for testing agent
capabilities across different domains:

- Eval: Base class for creating evaluations
- EvalResult: Individual evaluation result container
- EvalReport: Comprehensive evaluation report
- run_suite: Execute evaluation suites
- save_report: Persist evaluation results

The evaluation system supports testing across reasoning, coding, security,
and custom task domains.
"""

from .core import Eval, EvalReport, EvalResult, run_suite, save_report

__all__ = ["Eval", "EvalResult", "EvalReport", "run_suite", "save_report"]
