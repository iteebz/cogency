"""Tool chaining evaluation - migrated from archive."""

import os
import time
from typing import Any

from ..judges.claude_judge import ClaudeJudge
from ..logging import EvalLogger


class ToolChaining:
    """Test tool workflow sequences and data flow."""

    name = "tool_chaining"
    description = "Tool workflow sequences and data flow"

    def __init__(self):
        self.judge = ClaudeJudge()
        self.logger = EvalLogger()

    async def execute(self) -> dict[str, Any]:
        """Execute tool chaining evaluation."""
        from cogency import Agent

        print("🔗 Testing Tool Chaining...")
        start_time = time.time()

        # Multi-step tool chain from archive
        agent = Agent("chain_tester", tools=["files", "search", "shell"], max_iterations=15)

        query = """Complete this workflow step by step:
        1. Create a file called 'search_results.txt'
        2. Search for 'Python async programming best practices'
        3. Write the top 3 results to the file
        4. Use shell to count the lines in the file

        Execute each step and confirm completion before moving to the next."""

        result = await agent.run_async(query)
        response_lower = result.lower()

        # Check tool chain execution
        created_file = any(
            phrase in response_lower
            for phrase in ["created", "wrote", "made", "generated", "file", "search_results"]
        )
        performed_search = any(
            phrase in response_lower
            for phrase in ["search", "found", "results", "async", "python", "best practices"]
        )
        used_shell = any(
            phrase in response_lower
            for phrase in ["lines", "wc", "count", "shell", "command", "executed"]
        )

        # Check actual file creation and content
        file_exists = os.path.exists("search_results.txt")
        has_content = False
        if file_exists:
            try:
                with open("search_results.txt") as f:
                    content = f.read()
                    has_content = bool(content and content.strip())
                # Clean up
                os.remove("search_results.txt")
            except Exception:
                has_content = False

        # Scoring
        step_indicators = [created_file, performed_search, used_shell]
        file_indicators = [file_exists, has_content]

        steps_completed = sum(step_indicators)
        files_proper = sum(file_indicators)

        # Judge the tool chaining quality
        judge_result = await self._evaluate_chaining_response(query, result, step_indicators)

        # Log result
        self.logger.log_result(
            eval_name="tool_chain_search_file_shell",
            judge_result=judge_result,
            agent_metadata={
                "steps_completed": steps_completed,
                "file_creation": file_exists,
                "content_quality": has_content,
            },
            execution_time=time.time() - start_time,
        )

        # Pass if 2/3 steps indicated AND file exists OR all 3 steps indicated
        test_passed = (
            (steps_completed >= 2 and files_proper >= 1) or steps_completed == 3
        ) and judge_result.score.value >= 6.0

        step_score = steps_completed / 3.0
        file_score = files_proper / 2.0
        score = min(1.0, (step_score * 0.6) + (file_score * 0.4))

        duration = time.time() - start_time

        return {
            "name": self.name,
            "benchmark_passed": test_passed,
            "duration": duration,
            "summary": {
                "steps_completed": steps_completed,
                "files_proper": files_proper,
                "combined_score": score,
                "judge_score": judge_result.score.value,
            },
            "results": [
                {
                    "chain": "search-file-shell",
                    "query": query,
                    "response": result[:300] + "..." if len(result) > 300 else result,
                    "steps_completed": steps_completed,
                    "file_creation": file_exists,
                    "has_content": has_content,
                    "judge_score": judge_result.score.value,
                    "judge_reasoning": judge_result.score.reasoning,
                    "passed": test_passed,
                    "chain_steps": {
                        "created_file": created_file,
                        "performed_search": performed_search,
                        "used_shell": used_shell,
                        "file_exists": file_exists,
                        "has_content": has_content,
                    },
                }
            ],
            "metadata": {
                "evaluation_focus": "tool_chaining",
                "pattern_source": "archive/tool_chains.py",
                "data_flow": "search → file → shell",
                "logging_report": self.logger.generate_report(),
            },
        }

    async def _evaluate_chaining_response(self, query: str, response: str, step_indicators: list):
        """Evaluate tool chaining quality."""

        completed_steps = sum(step_indicators)

        criteria = f"""Tool Chaining Assessment:

Task: Multi-step tool chain (search → file → shell)
Steps Completed: {completed_steps}/3

Rate the agent's tool chaining capabilities:

1. **Data Flow Management**: Did it successfully pass data between tools?
2. **Sequential Execution**: Did it execute steps in proper order?
3. **Tool Integration**: Were tools used appropriately for each step?
4. **Output Quality**: Did it produce meaningful results at each stage?
5. **Chain Completion**: Was the full chain executed successfully?

Score 1-3: Poor tool coordination, broken data flow
Score 4-6: Partial chain execution with some data passing
Score 7-8: Good tool chaining with effective data flow
Score 9-10: Excellent tool orchestration with seamless data integration"""

        return await self.judge.evaluate(
            agent_response=response,
            test_case=query,
            criteria=criteria,
            context={
                "evaluation_focus": "tool_chaining",
                "completed_steps": completed_steps,
                "data_flow": "search → file → shell",
                "tools_used": ["files", "search", "shell"],
            },
        )
