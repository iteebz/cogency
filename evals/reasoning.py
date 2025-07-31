"""Basic reasoning evaluation - test agent's mathematical reasoning."""

from cogency import Agent
from cogency.evals import Eval, EvalResult


class ReasoningEval(Eval):
    """Test basic mathematical reasoning capabilities."""

    name = "reasoning"
    description = "Test agent's ability to solve simple math problems"

    async def run(self) -> EvalResult:
        agent = Agent("reasoning_tester", mode="fast", memory=False)

        query = "What is 15 * 8 + 23? Just give me the number."
        result = await agent.run(query)

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

        return self.check(actual, 143, {"query": query, "response": result})
