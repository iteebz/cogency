"""Reasoning chain evaluation - test agent's multi-step reasoning abilities."""

from cogency import Agent
from cogency.evals import Eval, EvalResult


class ReasoningChainEval(Eval):
    """Test agent's ability to perform multi-step logical reasoning."""

    name = "reasoning_chain"
    description = "Test agent's multi-step logical reasoning capabilities"

    async def run(self) -> EvalResult:
        agent = Agent("reasoning_chain_tester", mode="reasoning", memory=False)

        # Multi-step logic problem
        query = """
        If all birds can fly, and penguins are birds, but penguins cannot fly, 
        what can we conclude about the initial statement "all birds can fly"?
        Give me just your conclusion in one sentence.
        """

        result = await agent.run(query)

        # Expected reasoning: The initial statement is false/incorrect
        # Look for key indicators of logical reasoning
        correct_reasoning = any(
            keyword in result.lower()
            for keyword in [
                "false",
                "incorrect",
                "wrong",
                "not true",
                "contradiction",
                "invalid",
                "premise",
                "statement is",
            ]
        )

        # Check if penguin contradiction was recognized
        penguin_mentioned = "penguin" in result.lower()

        # Check for logical structure
        logical_structure = any(
            phrase in result.lower()
            for phrase in ["therefore", "because", "since", "this means", "contradiction"]
        )

        passed = correct_reasoning and penguin_mentioned
        score = 1.0 if passed else 0.7 if correct_reasoning else 0.3 if logical_structure else 0.0

        metadata = {
            "query": query.strip(),
            "response": result,
            "correct_reasoning": correct_reasoning,
            "penguin_mentioned": penguin_mentioned,
            "logical_structure": logical_structure,
        }

        return EvalResult(
            name=self.name,
            passed=passed,
            score=score,
            duration=0.0,
            expected="Identifies contradiction and concludes initial statement is false",
            actual=f"Correct reasoning: {correct_reasoning}, Mentioned penguins: {penguin_mentioned}",
            metadata=metadata,
        )
