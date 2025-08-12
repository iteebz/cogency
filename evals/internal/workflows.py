"""Complex workflow orchestration evaluation - migrated from archive."""

import os
import time
from typing import Any

from ..judges.claude_judge import ClaudeJudge
from ..logging import EvalLogger


class WorkflowOrchestration:
    """Test complex multi-tool workflow orchestration."""

    name = "workflow_orchestration"
    description = "Complex debugging and problem-solving workflows"

    def __init__(self):
        self.judge = ClaudeJudge()
        self.logger = EvalLogger()

    async def execute(self) -> dict[str, Any]:
        """Execute workflow orchestration evaluation."""
        from cogency import Agent

        print("🔄 Testing Workflow Orchestration...")
        start_time = time.time()

        # 7-step debugging workflow from archive
        agent = Agent("workflow_tester", tools=["files", "search", "shell"], max_iterations=15)

        query = """You need to debug a Python script issue. Follow this workflow:

        1. Create a test script 'debug_test.py' with this buggy code:
           ```python
           def calculate_average(numbers):
               total = sum(numbers)
               return total / len(numbers)

           data = []  # Empty list will cause division by zero
           result = calculate_average(data)
           print(f"Average: {result}")
           ```

        2. Run the script to see if there are any issues
        3. If there are issues, search online for 'Python division by zero handling'
        4. Fix the bug by adding proper error handling
        5. Test the fixed script with both valid data and empty list
        6. Create a summary file 'debug_summary.txt' explaining what was wrong and how you fixed it
        7. Clean up by removing both files

        Document each step and explain your debugging process."""

        result = await agent.run_async(query)
        response_lower = result.lower()

        # Workflow step validation
        created_script = any(
            phrase in response_lower
            for phrase in ["created", "wrote", "generated", "made", "debug_test", "script", "file"]
        )
        ran_initial_test = any(
            phrase in response_lower
            for phrase in ["ran", "executed", "run", "python", "script", "test", "tried"]
        )
        identified_issue = any(
            phrase in response_lower
            for phrase in ["issue", "bug", "problem", "error", "division", "zero", "empty", "fail"]
        )
        searched_solution = any(
            phrase in response_lower
            for phrase in ["search", "look", "find", "division", "zero", "handling", "solution"]
        )
        applied_fix = any(
            phrase in response_lower
            for phrase in ["fix", "handle", "try", "except", "catch", "check", "prevent", "solve"]
        )
        tested_fix = any(
            phrase in response_lower
            for phrase in ["test", "check", "verify", "valid", "empty", "work", "correct"]
        )
        created_summary = any(
            phrase in response_lower
            for phrase in ["summary", "explain", "document", "describe", "write", "create"]
        )
        cleaned_up = any(
            phrase in response_lower
            for phrase in ["clean", "remove", "delete", "clear", "cleanup", "tidy"]
        )

        # Check for debugging methodology
        systematic_approach = any(
            word in response_lower for word in ["step", "workflow", "process"]
        )
        explained_reasoning = any(
            word in response_lower for word in ["because", "reason", "explain"]
        )

        # Verify files don't exist (proper cleanup)
        files_cleaned = not os.path.exists("debug_test.py") and not os.path.exists(
            "debug_summary.txt"
        )

        # Score workflow completion
        workflow_steps = [
            created_script,
            ran_initial_test,
            identified_issue,
            searched_solution,
            applied_fix,
            tested_fix,
            created_summary,
            cleaned_up,
        ]

        step_completion = sum(workflow_steps) / len(workflow_steps)
        methodology_bonus = 0.15 if systematic_approach and explained_reasoning else 0.0
        min(1.0, step_completion + methodology_bonus)

        # Judge the workflow orchestration quality
        judge_result = await self._evaluate_workflow_response(query, result, workflow_steps)

        # Log result
        self.logger.log_result(
            eval_name="workflow_debugging_7_step",
            judge_result=judge_result,
            agent_metadata={
                "workflow_steps": len(workflow_steps),
                "methodology_bonus": methodology_bonus > 0,
            },
            execution_time=time.time() - start_time,
        )

        test_passed = (
            (step_completion >= 0.6 and systematic_approach)
            or step_completion >= 0.7
            or (files_cleaned and step_completion >= 0.5)
        ) and judge_result.score.value >= 6.0

        duration = time.time() - start_time

        return {
            "name": self.name,
            "benchmark_passed": test_passed,
            "duration": duration,
            "summary": {
                "workflow_completion": step_completion,
                "methodology_bonus": methodology_bonus > 0,
                "files_cleaned": files_cleaned,
                "judge_score": judge_result.score.value,
            },
            "results": [
                {
                    "workflow": "7-step debugging",
                    "query": query,
                    "response": result[:300] + "..." if len(result) > 300 else result,
                    "step_completion": step_completion,
                    "methodology_bonus": methodology_bonus,
                    "judge_score": judge_result.score.value,
                    "judge_reasoning": judge_result.score.reasoning,
                    "passed": test_passed,
                    "workflow_steps": {
                        "created_script": created_script,
                        "ran_initial_test": ran_initial_test,
                        "identified_issue": identified_issue,
                        "searched_solution": searched_solution,
                        "applied_fix": applied_fix,
                        "tested_fix": tested_fix,
                        "created_summary": created_summary,
                        "cleaned_up": cleaned_up,
                    },
                }
            ],
            "metadata": {
                "evaluation_focus": "workflow_orchestration",
                "pattern_source": "archive/complex_workflows.py",
                "tools_required": ["files", "search", "shell"],
                "logging_report": self.logger.generate_report(),
            },
        }

    async def _evaluate_workflow_response(self, query: str, response: str, workflow_steps: list):
        """Evaluate workflow orchestration quality."""

        completed_steps = sum(workflow_steps)
        total_steps = len(workflow_steps)

        criteria = f"""Workflow Orchestration Assessment:

Task: 7-step debugging workflow with multi-tool coordination
Steps Completed: {completed_steps}/{total_steps}

Rate the agent's workflow orchestration capabilities:

1. **Tool Coordination**: Did it effectively coordinate files, search, and shell tools?
2. **Workflow Adherence**: Did it follow the structured 7-step debugging process?
3. **Problem-Solving Quality**: Was the debugging approach sound and systematic?
4. **State Management**: Did it maintain workflow state across tool operations?
5. **Completion Quality**: Were all steps executed with proper cleanup?

Score 1-3: Poor tool coordination, minimal workflow adherence
Score 4-6: Partial workflow execution with some tool coordination
Score 7-8: Good workflow orchestration with effective tool usage
Score 9-10: Excellent systematic workflow with sophisticated tool coordination"""

        return await self.judge.evaluate(
            agent_response=response,
            test_case=query,
            criteria=criteria,
            context={
                "evaluation_focus": "workflow_orchestration",
                "steps_completed": completed_steps,
                "total_steps": total_steps,
                "tools_used": ["files", "search", "shell"],
            },
        )
