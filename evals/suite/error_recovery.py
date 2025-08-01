"""Error recovery evaluation - test agent's resilience to errors."""

from cogency import Agent
from evals.core import Eval, EvalResult


class ErrorRecoveryEval(Eval):
    """Test agent's ability to handle and recover from errors gracefully."""

    name = "error_recovery"
    description = "Test agent's error handling and recovery capabilities"

    async def run(self) -> EvalResult:
        agent = Agent("error_recovery_tester", mode="fast", memory=False)

        # Query that might cause issues but should be handled gracefully
        query = """
        Please access a non-existent file called 'missing_file.txt' and if that fails, 
        instead tell me what 2 + 2 equals. Handle any errors gracefully.
        """

        result = await agent.run(query)

        # Check if agent handled the error and provided the fallback answer
        provided_fallback = any(num in result for num in ["4", "four"])

        # Check if error was acknowledged
        error_acknowledged = any(
            keyword in result.lower()
            for keyword in [
                "error",
                "cannot",
                "unable",
                "not found",
                "missing",
                "fail",
                "does not exist",
            ]
        )

        # Check that it didn't crash (we got a response)
        no_crash = len(result.strip()) > 0

        # Graceful handling means acknowledging error AND providing fallback
        graceful_handling = error_acknowledged and provided_fallback and no_crash

        passed = graceful_handling
        score = (
            1.0
            if passed
            else 0.7
            if (error_acknowledged and no_crash)
            else 0.3
            if no_crash
            else 0.0
        )

        metadata = {
            "query": query.strip(),
            "response": result,
            "provided_fallback": provided_fallback,
            "error_acknowledged": error_acknowledged,
            "no_crash": no_crash,
            "graceful_handling": graceful_handling,
        }

        return EvalResult(
            name=self.name,
            passed=passed,
            score=score,
            duration=0.0,
            expected="Agent handles file error gracefully and provides fallback answer (4)",
            actual=f"Graceful: {graceful_handling}, Fallback: {provided_fallback}, Error ack: {error_acknowledged}",
            metadata=metadata,
        )
