"""Complex debugging workflows evaluation."""

from cogency import Agent
from cogency.tools.files import Files
from cogency.tools.search import Search
from cogency.tools.shell import Shell

from ...core import Eval, FailureType


class ComplexWorkflows(Eval):
    """Test agent's ability to handle complex debugging workflows."""

    name = "complex_workflows"
    description = "Test complex debugging and problem-solving workflows"

    async def run(self):
        agent = Agent(
            "workflow_tester",
            tools=[Files(), Search(), Shell()],
            mode="fast",
            memory=False,
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
        import os

        files_cleaned = not os.path.exists("debug_test.py") and not os.path.exists(
            "debug_summary.txt"
        )

        metadata = {
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
            "systematic_approach": systematic_approach,
            "explained_reasoning": explained_reasoning,
            "files_cleaned": files_cleaned,
        }

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

        if step_completion >= 0.7 and files_cleaned:
            passed = final_score >= 0.8
            result_obj = self.check(
                "Complex workflow completed", "Complex workflow completed", metadata
            )
            result_obj.score = final_score
            result_obj.passed = passed
            return result_obj
        else:
            missing_steps = []
            if not created_script:
                missing_steps.append("script creation")
            if not ran_initial_test:
                missing_steps.append("initial testing")
            if not identified_issue:
                missing_steps.append("issue identification")
            if not searched_solution:
                missing_steps.append("solution research")
            if not applied_fix:
                missing_steps.append("bug fix")
            if not tested_fix:
                missing_steps.append("fix verification")
            if not created_summary:
                missing_steps.append("documentation")
            if not cleaned_up:
                missing_steps.append("cleanup")
            if not files_cleaned:
                missing_steps.append("proper file removal")

            failure_result = self.fail(
                f"Incomplete workflow - missing: {', '.join(missing_steps)}", metadata
            )
            failure_result.failure_type = FailureType.LOGIC
            return failure_result
