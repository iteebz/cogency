"""Memory persistence evaluation."""

from ..eval import Eval, EvalResult


class MemoryPersistence(Eval):
    """Test agent's memory and information persistence."""

    name = "memory_persistence"
    description = "Test agent's ability to remember context across interactions"

    async def run(self) -> EvalResult:
        test_cases = [
            "Remember this number: 42. What mathematical operations can we do with it?",
            "I told you to remember 42. What was that number?",
            "Use the number I mentioned earlier to solve: X + 8 = 50",
            "What number did I ask you to remember at the start?",
            "Create a story involving the special number from our conversation",
        ]

        def validator(response, test_case):
            return "42" in response and len(response) > 20

        return await self.run_test_cases(test_cases, validator, "memory_tester", memory=True)
