"""Memory persistence evaluation."""

from cogency import Agent

from ...core import Eval, EvalResult


class MemoryPersistence(Eval):
    """Test agent's ability to maintain memory across interactions."""

    name = "memory_persistence"
    description = "Test memory retention and retrieval"

    # Declarative test cases for memory operations
    test_cases = [
        {
            "name": "Store personal facts",
            "query": "Remember that my favorite color is blue and my pet's name is Whiskers.",
            "expected": True,
            "parser": "_check_storage",
        },
        {
            "name": "Recall favorite color",
            "query": "What is my favorite color?",
            "expected": True,
            "parser": "_check_color_recall",
        },
        {
            "name": "Recall pet name",
            "query": "What is my pet's name?",
            "expected": True,
            "parser": "_check_pet_recall",
        },
        {
            "name": "Recall both facts together",
            "query": "What is my favorite color and what is my pet's name?",
            "expected": True,
            "parser": "_check_combined_recall",
        },
    ]

    async def run(self) -> EvalResult:
        self.agent = Agent("memory_tester", memory=True, mode="fast", max_iterations=5)

        await self.run_test_cases(self.agent, self.test_cases)
        return self.finalize_result()

    def _check_storage(self, response: str) -> bool:
        """Check storage operation - always succeeds if no error."""
        return True

    def _check_color_recall(self, response: str) -> bool:
        """Check if favorite color is recalled."""
        return "blue" in response.lower()

    def _check_pet_recall(self, response: str) -> bool:
        """Check if pet name is recalled."""
        return "whiskers" in response.lower()

    def _check_combined_recall(self, response: str) -> bool:
        """Check if both facts are recalled together."""
        response_lower = response.lower()
        has_color = "blue" in response_lower
        has_pet = "whiskers" in response_lower
        return has_color and has_pet
