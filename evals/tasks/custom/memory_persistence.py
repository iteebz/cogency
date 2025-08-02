"""Memory persistence evaluation."""

from cogency import Agent

from ...core import Eval, EvalResult


class MemoryPersistence(Eval):
    """Test agent's ability to maintain memory across interactions."""

    name = "memory_persistence"
    description = "Test memory retention and retrieval"

    async def run(self) -> EvalResult:
        agent = Agent("memory_tester", memory=True, mode="fast")

        # First interaction - store information
        await agent.run("Remember that my favorite color is blue and my pet's name is Whiskers.")

        # Second interaction - test recall
        result = await agent.run("What is my favorite color and what is my pet's name?")

        # Check if agent recalled both pieces of information
        result_lower = result.lower()
        has_color = "blue" in result_lower
        has_pet_name = "whiskers" in result_lower

        if has_color and has_pet_name:
            score = 1.0
            passed = True
        elif has_color or has_pet_name:
            score = 0.5
            passed = False
        else:
            score = 0.0
            passed = False

        metadata = {
            "response": result,
            "recalled_color": has_color,
            "recalled_pet_name": has_pet_name,
        }

        return EvalResult(
            name=self.name,
            passed=passed,
            score=score,
            duration=0.0,  # Will be set by base class
            expected="Recall both stored facts",
            actual=f"Color: {has_color}, Pet: {has_pet_name}",
            metadata=metadata,
        )
