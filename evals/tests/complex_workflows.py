"""Complex debugging workflows evaluation."""

import os

from cogency.tools.files import Files
from cogency.tools.search import Search
from cogency.tools.shell import Shell

from ..eval import Eval, EvalResult


class ComplexWorkflows(Eval):
    """Test agent's ability to handle complex debugging workflows."""

    name = "complex_workflows"
    description = "Test complex debugging and problem-solving workflows"

    async def run(self) -> EvalResult:
        agent = self.create_agent(
            "workflow_tester",
            tools=[Files(), Search(), Shell()],
            max_iterations=15,
        )

        # Create a complex debugging scenario
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

        # Check workflow completion steps
        created_script = any(
            word in response_lower for word in ["created", "debug_test.py", "script"]
        )
        ran_initial_test = any(word in response_lower for word in ["ran", "executed", "python"])
        identified_issue = any(
            word in response_lower for word in ["issue", "bug", "problem", "error"]
        )
        searched_solution = any(
            word in response_lower for word in ["search", "division by zero", "handling"]
        )
        applied_fix = any(
            word in response_lower for word in ["fix", "error handling", "try", "except"]
        )
        tested_fix = any(word in response_lower for word in ["test", "valid", "empty"])
        created_summary = any(
            word in response_lower for word in ["summary", "debug_summary", "explained"]
        )
        cleaned_up = any(word in response_lower for word in ["clean", "removed", "deleted"])

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

        # Score based on workflow completion
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

        # Bonus for methodology and reasoning
        methodology_bonus = 0.0
        if systematic_approach and explained_reasoning:
            methodology_bonus = 0.15

        final_score = min(1.0, step_completion + methodology_bonus)
        passed = step_completion >= 0.8 and files_cleaned

        agent_logs = agent.logs() if hasattr(agent, "logs") else []

        return EvalResult(
            name=self.name,
            passed=passed,
            score=final_score,
            duration=0.0,
            traces=[
                {
                    "query": query,
                    "response": result,
                    "created_script": created_script,
                    "ran_initial_test": ran_initial_test,
                    "identified_issue": identified_issue,
                    "searched_solution": searched_solution,
                    "applied_fix": applied_fix,
                    "tested_fix": tested_fix,
                    "created_summary": created_summary,
                    "cleaned_up": cleaned_up,
                    "logs": agent_logs,
                }
            ],
            metadata={
                "created_script": created_script,
                "ran_initial_test": ran_initial_test,
                "identified_issue": identified_issue,
                "searched_solution": searched_solution,
                "applied_fix": applied_fix,
                "tested_fix": tested_fix,
                "created_summary": created_summary,
                "cleaned_up": cleaned_up,
                "systematic_approach": systematic_approach,
                "explained_reasoning": explained_reasoning,
                "files_cleaned": files_cleaned,
            },
        )
