"""Basic reasoning evaluation - test agent's mathematical reasoning."""

from time import perf_counter

from cogency import Agent
from evals.core import Eval, EvalResult


class ReasoningEval(Eval):
    """Test basic mathematical reasoning capabilities."""

    name = "reasoning"
    description = "Test agent's ability to solve simple math problems"

    async def run(self) -> EvalResult:
        # Time agent creation
        t0 = perf_counter()
        agent = Agent("reasoning_tester", mode="fast", memory=False)
        t1 = perf_counter()

        # Time query execution
        query = "What is 15 * 8 + 23? Just give me the number."
        result = await agent.run(query)
        t2 = perf_counter()

        # Extract number from response
        try:
            # Look for the number 143 in the response
            import re

            numbers = re.findall(r"\b\d+\b", result)
            if "143" in numbers:
                actual = 143
            else:
                actual = int(numbers[-1]) if numbers else None
        except (ValueError, IndexError):
            return self.fail("Could not parse number from response", {"response": result})

        # Add timing breakdown to metadata
        metadata = {
            "query": query,
            "response": result,
            "timing": {
                "agent_creation": f"{t1-t0:.3f}s",
                "query_execution": f"{t2-t1:.3f}s",
                "total": f"{t2-t0:.3f}s",
            },
        }

        return self.check(actual, 143, metadata)
