"""Base evaluation class."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from resilient_result import Result

from cogency.observe.timer import timer

from .models import EvalResult, FailureType, SubCaseResult


class Eval(ABC):
    """Base class for all evaluations.

    Provides test case management, scoring, and result formatting.
    """

    name: str = "unnamed_eval"
    description: str = "No description"

    def __init__(self):
        self._timer = None
        self._sub_cases = []

    @abstractmethod
    async def run(self) -> EvalResult:
        """Execute the evaluation and return results."""
        pass

    def check_sub_case(
        self, name: str, actual: Any, expected: Any, live_output: bool = True, response: str = ""
    ) -> bool:
        """Check sub-case result and optionally print feedback.

        Args:
            name: Test case name
            actual: Actual result
            expected: Expected result
            live_output: Print result immediately
            response: Original LLM response for debugging

        Returns:
            True if test passed
        """
        passed = actual == expected

        sub_case = SubCaseResult(name=name, passed=passed, expected=expected, actual=actual)
        self._sub_cases.append(sub_case)

        if live_output:
            status = "✓" if passed else "✗"
            if passed:
                print(f"  {status} {name}: PASS", flush=True)
            else:
                # Show truncated response snippet for debugging
                snippet = response[:150] + "..." if len(response) > 150 else response
                snippet = snippet.replace('\n', ' ').strip()
                print(f"  {status} {name} → FAIL - Response: \"{snippet}\"", flush=True)

        return passed

    def fail_sub_case(
        self,
        name: str,
        error: str,
        failure_type: Optional[FailureType] = None,
        live_output: bool = True,
    ) -> bool:
        """Record a failed sub-case and optionally print live feedback."""
        sub_case = SubCaseResult(name=name, passed=False, error=error, failure_type=failure_type)
        self._sub_cases.append(sub_case)

        if live_output:
            print(f"  ✗ {name} → {error}", flush=True)

        return False

    def check(self, actual: Any, expected: Any, metadata: Optional[Dict] = None) -> EvalResult:
        """Create EvalResult from comparison."""
        passed = actual == expected
        score = 1.0 if passed else 0.0
        duration = self._timer() if self._timer else 0.0

        return EvalResult(
            name=self.name,
            passed=passed,
            score=score,
            duration=duration,
            expected=expected,
            actual=actual,
            metadata=metadata or {},
            sub_cases=self._sub_cases.copy(),
        )

    async def run_test_cases(self, agent_factory, test_cases: List[Dict]) -> None:
        """Run test cases with fresh agent instances."""
        for case in test_cases:
            try:
                # Create fresh agent for each test case to prevent context pollution
                agent = agent_factory()
                result = await agent.run_async(case["query"])
                parser_method = getattr(self, case["parser"])
                actual = parser_method(result)
                self.check_sub_case(case["name"], actual, case["expected"], response=result)
            except Exception as e:
                self.fail_sub_case(case["name"], f"error: {e}", FailureType.ERROR)

    def finalize_result(self, metadata: Optional[Dict] = None) -> EvalResult:
        """Create final EvalResult from sub-cases."""
        if not self._sub_cases:
            return self.fail("No sub-cases executed", metadata)

        passed_count = sum(1 for sc in self._sub_cases if sc.passed)
        total_count = len(self._sub_cases)
        passed = passed_count == total_count
        score = passed_count / total_count if total_count > 0 else 0.0
        duration = self._timer() if self._timer else 0.0

        percentage = int(score * 100)
        print(
            f"  Score: {percentage}% • {passed_count}/{total_count} passed • {duration:.1f}s\n",
            flush=True,
        )

        return EvalResult(
            name=self.name,
            passed=passed,
            score=score,
            duration=duration,
            metadata=metadata or {},
            sub_cases=self._sub_cases.copy(),
        )

    def fail(
        self,
        error: str,
        metadata: Optional[Dict] = None,
        failure_type: Optional[FailureType] = None,
    ) -> EvalResult:
        """Helper to create failed EvalResult."""
        duration = self._timer() if self._timer else 0.0

        return EvalResult(
            name=self.name,
            passed=False,
            score=0.0,
            duration=duration,
            error=error,
            failure_type=failure_type,
            metadata=metadata or {},
            sub_cases=self._sub_cases.copy(),
        )

    async def execute(self) -> Result[EvalResult, str]:
        """Execute eval with error handling."""
        self._timer = timer(f"eval_{self.name}")

        try:
            result = await self.run()
            return Result.ok(result)
        except Exception as e:
            error_result = self.fail(f"{type(e).__name__}: {e}")
            return Result.ok(error_result)
