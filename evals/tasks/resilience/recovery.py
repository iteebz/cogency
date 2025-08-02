"""Error recovery evaluation."""

from cogency import Agent
from cogency.tools.files import Files
from cogency.tools.shell import Shell

from ...core import Eval, FailureType


class ErrorRecovery(Eval):
    """Test agent's ability to recover from errors and continue execution."""

    name = "error_recovery"
    description = "Test error handling patterns and recovery strategies"

    async def run(self):
        agent = Agent("recovery_tester", tools=[Files(), Shell()], mode="fast", memory=False)

        # Design a task that will encounter errors but can be recovered from
        query = """Complete this multi-step task, handling any errors gracefully:
        
        1. Try to read file 'nonexistent.txt' (will fail)
        2. When that fails, create the file with content 'Recovery test'
        3. Read the file you just created to verify it worked
        4. Try to run command 'invalid-command-xyz' (will fail)  
        5. When that fails, run 'echo Successfully recovered' instead
        6. Clean up by removing the file you created
        
        For each step, report what happened and how you handled any failures."""

        result = await agent.run(query)
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
            word in response_lower for word in ["invalid", "command", "not found"]
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
        import os

        file_properly_cleaned = not os.path.exists("nonexistent.txt")

        metadata = {
            "query": query,
            "response": result,
            "attempted_nonexistent": attempted_nonexistent,
            "created_recovery_file": created_recovery_file,
            "verified_file_content": verified_file_content,
            "handled_invalid_command": handled_invalid_command,
            "successful_recovery": successful_recovery,
            "cleaned_up": cleaned_up,
            "explicit_error_handling": explicit_error_handling,
            "continued_after_errors": continued_after_errors,
            "file_properly_cleaned": file_properly_cleaned,
        }

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

        if recovery_score >= 0.7 and continued_after_errors and file_properly_cleaned:
            passed = recovery_score >= 0.8
            result_obj = self.check(
                "Error recovery completed", "Error recovery completed", metadata
            )
            result_obj.score = recovery_score
            result_obj.passed = passed
            return result_obj
        else:
            missing_steps = []
            if not attempted_nonexistent:
                missing_steps.append("initial error attempt")
            if not created_recovery_file:
                missing_steps.append("file creation recovery")
            if not handled_invalid_command:
                missing_steps.append("command error handling")
            if not successful_recovery:
                missing_steps.append("successful recovery")
            if not continued_after_errors:
                missing_steps.append("continuation after errors")
            if not file_properly_cleaned:
                missing_steps.append("cleanup")

            failure_result = self.fail(
                f"Incomplete error recovery - missing: {', '.join(missing_steps)}", metadata
            )
            failure_result.failure_type = FailureType.LOGIC
            return failure_result
