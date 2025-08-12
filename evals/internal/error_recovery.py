"""Error recovery evaluation - migrated from archive."""

import os
import time
from typing import Any

from ..judges.claude_judge import ClaudeJudge
from ..logging import EvalLogger


class ErrorRecovery:
    """Test agent's ability to recover from errors and continue execution."""

    name = "error_recovery"
    description = "Error handling patterns and recovery strategies"

    def __init__(self):
        self.judge = ClaudeJudge()
        self.logger = EvalLogger()

    async def execute(self) -> dict[str, Any]:
        """Execute error recovery evaluation."""
        from cogency import Agent

        print("🔧 Testing Error Recovery...")
        start_time = time.time()

        agent = Agent("recovery_tester", tools=["files", "shell"], max_iterations=15)

        # Design a task that will encounter errors but can be recovered from
        query = """You must complete this exact multi-step error recovery task. Execute each step in order:

        Step 1: Use files tool to read 'nonexistent.txt' (this will fail - that's expected)
        Step 2: When step 1 fails, use files tool to create 'nonexistent.txt' with content 'Recovery test'
        Step 3: Use files tool to read the file you just created to verify the content
        Step 4: Use shell tool to run 'invalid-command-xyz' (this will fail - that's expected)
        Step 5: When step 4 fails, use shell tool to run 'echo Successfully recovered'
        Step 6: Use shell tool to run 'rm nonexistent.txt' to clean up

        Execute all 6 steps. Report what happens at each step and how you handle failures."""

        result = await agent.run_async(query)
        response_lower = result.lower()

        # Check for evidence of error handling and recovery
        attempted_nonexistent = any(
            word in response_lower for word in ["nonexistent", "not found", "doesn't exist"]
        )
        created_recovery_file = any(word in response_lower for word in ["created", "recovery test"])
        verified_file_content = any(
            word in response_lower for word in ["recovery test", "verified", "content"]
        )
        handled_invalid_command = any(
            word in response_lower
            for word in ["invalid", "command", "not found", "failed", "error"]
        )
        successful_recovery = any(
            word in response_lower for word in ["successfully recovered", "echo"]
        )
        cleaned_up = any(word in response_lower for word in ["removed", "deleted", "clean"])

        # Check for error handling patterns
        explicit_error_handling = any(
            word in response_lower for word in ["error", "failed", "exception", "handle"]
        )
        continued_after_errors = created_recovery_file and successful_recovery

        # Verify file was actually cleaned up (shouldn't exist)
        file_properly_cleaned = not os.path.exists("nonexistent.txt")

        # Score based on recovery capabilities
        recovery_steps = [
            attempted_nonexistent,
            created_recovery_file,
            verified_file_content,
            handled_invalid_command,
            successful_recovery,
            cleaned_up,
        ]

        recovery_score = sum(recovery_steps) / len(recovery_steps)

        # Bonus for explicit error handling and continuation
        if explicit_error_handling and continued_after_errors:
            recovery_score = min(1.0, recovery_score + 0.1)

        # Judge the error recovery quality
        judge_result = await self._evaluate_recovery_response(query, result, recovery_steps)

        # Log result
        self.logger.log_result(
            eval_name="error_recovery_6_step",
            judge_result=judge_result,
            agent_metadata={
                "recovery_steps": sum(recovery_steps),
                "continued_after_errors": continued_after_errors,
                "file_cleanup": file_properly_cleaned,
            },
            execution_time=time.time() - start_time,
        )

        test_passed = (
            recovery_score >= 0.8 and continued_after_errors and file_properly_cleaned
        ) and judge_result.score.value >= 6.0

        duration = time.time() - start_time

        return {
            "name": self.name,
            "benchmark_passed": test_passed,
            "duration": duration,
            "summary": {
                "recovery_score": recovery_score,
                "continued_after_errors": continued_after_errors,
                "file_cleanup": file_properly_cleaned,
                "judge_score": judge_result.score.value,
            },
            "results": [
                {
                    "scenario": "6-step error recovery",
                    "query": query,
                    "response": result[:300] + "..." if len(result) > 300 else result,
                    "recovery_score": recovery_score,
                    "judge_score": judge_result.score.value,
                    "judge_reasoning": judge_result.score.reasoning,
                    "passed": test_passed,
                    "recovery_steps": {
                        "attempted_nonexistent": attempted_nonexistent,
                        "created_recovery_file": created_recovery_file,
                        "verified_file_content": verified_file_content,
                        "handled_invalid_command": handled_invalid_command,
                        "successful_recovery": successful_recovery,
                        "cleaned_up": cleaned_up,
                        "explicit_error_handling": explicit_error_handling,
                        "continued_after_errors": continued_after_errors,
                        "file_properly_cleaned": file_properly_cleaned,
                    },
                }
            ],
            "metadata": {
                "evaluation_focus": "error_recovery",
                "pattern_source": "archive/error_recovery.py",
                "recovery_pattern": "fail → recover → verify → continue → cleanup",
                "logging_report": self.logger.generate_report(),
            },
        }

    async def _evaluate_recovery_response(self, query: str, response: str, recovery_steps: list):
        """Evaluate error recovery quality."""

        completed_steps = sum(recovery_steps)

        criteria = f"""Error Recovery Assessment:

Task: 6-step error recovery with intentional failures
Recovery Steps Completed: {completed_steps}/6

Rate the agent's error recovery capabilities:

1. **Error Recognition**: Did it properly identify and acknowledge errors?
2. **Recovery Strategy**: Did it implement appropriate recovery actions?
3. **Continuation**: Did it continue workflow execution after recovering?
4. **Resilience**: Did it handle multiple different types of errors?
5. **Cleanup**: Did it properly clean up after recovery operations?

Score 1-3: Poor error handling, fails to recover or continue
Score 4-6: Partial recovery with some continuation capability
Score 7-8: Good error recovery with systematic continuation
Score 9-10: Excellent resilience with comprehensive error handling"""

        return await self.judge.evaluate(
            agent_response=response,
            test_case=query,
            criteria=criteria,
            context={
                "evaluation_focus": "error_recovery",
                "recovery_steps_completed": completed_steps,
                "total_steps": len(recovery_steps),
                "error_types": ["file_not_found", "invalid_command"],
            },
        )
