"""Mathematical reasoning evaluation."""

from cogency import Agent

from ...core import Eval, EvalResult


class MathReasoning(Eval):
    """Test basic mathematical reasoning capabilities."""

    name = "math_reasoning"
    description = "Test agent's ability to solve simple math problems"

    async def run(self) -> EvalResult:
        agent = Agent("math_tester", mode="fast", memory=False)

        query = "What is 15 * 8 + 23? Just give me the number."
        result = await agent.run(query)

        # Extract number from response
        try:
            import re

            numbers = re.findall(r"\b\d+\b", result)
            if "143" in numbers:
                actual = 143
            else:
                actual = int(numbers[-1]) if numbers else None
        except (ValueError, IndexError):
            return self.fail("Could not parse number from response", {"response": result})

        metadata = {
            "query": query,
            "response": result,
        }

        return self.check(actual, 143, metadata)
