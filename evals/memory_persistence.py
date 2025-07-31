"""Memory persistence evaluation - test agent's ability to remember across interactions."""

from cogency import Agent
from cogency.evals import Eval, EvalResult


class MemoryPersistenceEval(Eval):
    """Test agent's memory persistence across multiple interactions."""

    name = "memory_persistence"
    description = "Test agent's ability to remember information across interactions"

    async def run(self) -> EvalResult:
        # Create agent with memory enabled and Gemini LLM
        from cogency.services.llm import Gemini
        agent = Agent("memory_tester", mode="fast", memory=True, llm=Gemini())

        # First interaction - store information
        first_query = "Remember that my favorite color is blue and my lucky number is 7."
        first_response = await agent.run(first_query)

        # Second interaction - test recall
        second_query = "What is my favorite color and lucky number?"
        second_response = await agent.run(second_query)

        # Check if agent remembered the information
        remembered_color = "blue" in second_response.lower()
        remembered_number = "7" in second_response

        passed = remembered_color and remembered_number
        score = 1.0 if passed else 0.5 if (remembered_color or remembered_number) else 0.0

        metadata = {
            "first_query": first_query,
            "first_response": first_response,
            "second_query": second_query,
            "second_response": second_response,
            "remembered_color": remembered_color,
            "remembered_number": remembered_number,
        }

        return EvalResult(
            name=self.name,
            passed=passed,
            score=score,
            duration=0.0,
            expected="Agent remembers favorite color (blue) and lucky number (7)",
            actual=f"Color: {remembered_color}, Number: {remembered_number}",
            metadata=metadata,
        )
