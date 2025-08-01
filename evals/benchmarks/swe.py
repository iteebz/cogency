"""SWE benchmark - Software engineering task completion."""

import asyncio
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict

# Add root to path for evals imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


from evals.core.base import Eval, EvalResult


class SWE(Eval):
    """Test agent's ability to complete software engineering tasks."""

    name = "swe"
    description = "Software engineering task completion benchmark"

    def __init__(self):
        super().__init__()
        self.results_dir = Path(".cogency/evals")
        self.results_dir.mkdir(exist_ok=True)
        self.fixtures_dir = Path("evals/fixtures/swe")

    async def run(self) -> EvalResult:
        """Run SWE tasks using static fixtures and diff validation."""

        # Load fixture-based tasks
        fixture_dirs = ["offby", "email", "optimize", "empty", "memo"]

        results = []

        for i, fixture_name in enumerate(fixture_dirs, 1):
            print(f"🔄 [{i}/{len(fixture_dirs)}] Running: {fixture_name}")

            try:
                task_result = await self._run_fixture_task(fixture_name)
                results.append(task_result)
                self._log_task_result(task_result)

                # Show immediate result
                status = "✅ PASS" if task_result["passed"] else "❌ FAIL"
                score = task_result["score"]
                print(f"   {status} - Score: {score:.1%}")

            except Exception as e:
                print(f"   ❌ ERROR: {e}")
                task_result = {
                    "task_id": fixture_name,
                    "passed": False,
                    "score": 0.0,
                    "error": str(e),
                }
                results.append(task_result)
                self._log_task_result(task_result)

        # Aggregate results
        total_score = sum(r["score"] for r in results)
        avg_score = total_score / len(results) if results else 0.0
        passed_count = sum(1 for r in results if r.get("passed", False))

        final_result = EvalResult(
            name=self.name,
            passed=avg_score >= 0.15,  # 15% pass rate target
            score=avg_score,
            duration=0.0,
            expected="≥15% completion rate on software engineering tasks",
            actual=f"{passed_count}/{len(results)} tasks completed ({avg_score:.1%})",
            metadata={
                "tasks_completed": passed_count,
                "total_tasks": len(results),
                "completion_rate": avg_score,
                "individual_results": results,
            },
        )

        self._log_final_result(final_result)
        return final_result

    async def _run_fixture_task(self, fixture_name: str) -> Dict[str, Any]:
        """Run a single fixture-based SWE task."""
        fixture_dir = self.fixtures_dir / fixture_name

        # Load issue description
        issue_path = fixture_dir / "issue.md"
        expected_diff_path = fixture_dir / "expected.diff"

        if not issue_path.exists() or not expected_diff_path.exists():
            raise FileNotFoundError(f"Missing fixtures in {fixture_dir}")

        issue_content = issue_path.read_text()
        expected_diff = expected_diff_path.read_text()

        # Create temporary workspace
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Copy source files to temp workspace
            for src_file in fixture_dir.glob("*.py"):
                dest_file = temp_path / src_file.name
                dest_file.write_text(src_file.read_text())

            # Create agent with Files tool configured for this workspace
            from cogency import Agent
            from cogency.tools.files import Files

            workspace_files_tool = Files(base_dir=str(temp_path))
            agent = Agent("swe_agent", tools=[workspace_files_tool])

            # Construct prompt for agent
            prompt = f"""
            You are working on a software engineering task. Here's the issue description:
            
            {issue_content}
            
            The workspace is located at: {temp_path}
            
            Use the Files tool to explore the codebase, understand the issue, and make the necessary changes.
            Provide a unified diff of your changes when complete.
            """

            # Run agent
            try:
                response = await agent.run(prompt)
                if not response:
                    response = "No response generated"
            except Exception as e:
                response = f"Agent execution failed: {e}"

            # Extract and validate diff
            diff_match_score = self._validate_diff_similarity(response, expected_diff)

            return {
                "task_id": fixture_name,
                "passed": diff_match_score >= 0.7,  # 70% similarity threshold
                "score": diff_match_score,
                "issue": issue_content,
                "agent_response": response,
                "expected_diff": expected_diff,
                "similarity_score": diff_match_score,
            }

    def _validate_diff_similarity(self, agent_response: str, expected_diff: str) -> float:
        """Calculate similarity score between agent response and expected diff."""
        # Simple keyword-based similarity for now
        # In production, could use more sophisticated diff parsing

        agent_lower = agent_response.lower()
        expected_lines = expected_diff.strip().split("\n")

        # Look for key change indicators in expected diff
        key_changes = []
        for line in expected_lines:
            if line.startswith("+") and not line.startswith("+++"):
                # Extract meaningful content from added lines
                content = line[1:].strip()
                if content and not content.startswith("#"):
                    key_changes.append(content)

        if not key_changes:
            return 0.0

        # Check how many key changes appear in agent response
        matches = 0
        for change in key_changes:
            if change.lower() in agent_lower:
                matches += 1

        return matches / len(key_changes)

    def _log_task_result(self, task_result: dict):
        """Log individual task result."""
        timestamp = int(self.start_time) if self.start_time else 0
        log_file = self.results_dir / f"swe_task_{task_result['task_id']}_{timestamp}.json"

        with open(log_file, "w") as f:
            json.dump(task_result, f, indent=2)

    def _log_final_result(self, result: EvalResult):
        """Log final aggregated result."""
        timestamp = int(self.start_time) if self.start_time else 0
        log_file = self.results_dir / f"swe_final_{timestamp}.json"

        with open(log_file, "w") as f:
            json.dump(result.model_dump(), f, indent=2)


async def main():
    """Run SWE benchmark directly."""
    print("🚀 Running SWE Benchmark")
    print("=" * 50)

    swe = SWE()
    result = await swe.run()

    print("\n" + "=" * 50)
    print("📊 Final Results:")
    print(f"✅ Passed: {result.passed}")
    print(f"📈 Score: {result.score:.2%}")
    print(f"🎯 Expected: {result.expected}")
    print(f"📋 Actual: {result.actual}")

    return result.passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
