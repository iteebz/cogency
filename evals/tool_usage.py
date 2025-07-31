"""Tool usage evaluation - test agent's ability to use tools effectively."""

from time import perf_counter

from cogency import Agent
from cogency.evals import Eval, EvalResult
from cogency.tools.calculator import Calculator


class ToolUsageEval(Eval):
    """Test agent's ability to use tools for complex calculations."""

    name = "tool_usage"
    description = "Test agent's ability to use calculator tool for complex math"

    async def run(self) -> EvalResult:
        t0 = perf_counter()
        agent = Agent("tool_tester", mode="fast", memory=False, tools=[Calculator()])

        # Complex calculation that requires multiple steps
        query = "Calculate the compound interest on $1000 at 5% annual rate for 3 years using A = P(1 + r)^t. Show your work."
        result = await agent.run(query)
        duration = perf_counter() - t0

        # Expected: A = 1000(1 + 0.05)^3 = 1000(1.05)^3 = 1000(1.157625) = 1157.625
        expected_final = 1157.625

        # Check if the calculation was performed correctly
        # Look for the final amount in the response
        import re

        # Look for numbers that might be the final result
        numbers = re.findall(r"\d+\.?\d*", result.replace("$", "").replace(",", ""))
        found_correct = False

        for num_str in numbers:
            try:
                num = float(num_str)
                # Allow for small rounding differences
                if abs(num - expected_final) < 1.0:
                    found_correct = True
                    break
            except ValueError:
                continue

        # Also check if tool usage is mentioned
        tool_used = any(
            keyword in result.lower()
            for keyword in ["calculat", "tool", "step", "work", "1.05", "1157"]
        )

        passed = found_correct and tool_used
        score = 1.0 if passed else 0.5 if (found_correct or tool_used) else 0.0

        metadata = {
            "query": query,
            "response": result,
            "expected_result": expected_final,
            "found_correct_result": found_correct,
            "tool_usage_detected": tool_used,
            "numbers_found": numbers,
        }

        return EvalResult(
            name=self.name,
            passed=passed,
            score=score,
            duration=duration,
            expected="Correct compound interest calculation using tools",
            actual=f"Correct result: {found_correct}, Tool used: {tool_used}",
            metadata=metadata,
        )
