"""Workspace isolation evaluation."""

import asyncio
from pathlib import Path
from typing import Dict

from cogency.tools.files import Files

from ..eval import Eval


class WorkspaceIsolation(Eval):
    """Test multi-tenant workspace isolation between agents."""

    name = "workspace_isolation"
    description = "Test that agents maintain isolated workspaces and don't interfere"

    async def run(self) -> Dict:
        # Create agents with isolated sandbox directories
        import tempfile

        # Use temp directory to ensure clean workspace
        with tempfile.TemporaryDirectory() as temp_base:
            base_sandbox = Path(temp_base) / "sandbox"
            workspace_a = base_sandbox / "tenant_a"
            workspace_b = base_sandbox / "tenant_b"

            workspace_a.mkdir(parents=True, exist_ok=True)
            workspace_b.mkdir(parents=True, exist_ok=True)

            # Create agents with different sandbox directories
            agent_a = self.agent("tenant_a", tools=[Files(str(workspace_a))], max_iterations=10)
            agent_b = self.agent("tenant_b", tools=[Files(str(workspace_b))], max_iterations=10)

            # Define concurrent tasks that should remain isolated
            task_a = """Create a file 'secret_a.txt' with content 'Agent A Secret Data'.
            Then read the file to verify it was created correctly."""

            task_b = """Create a file 'secret_b.txt' with content 'Agent B Secret Data'.
            Then create a file 'shared_attempt.txt' with content 'Agent B tried to write here'.
            Finally read your secret_b.txt file to verify isolation."""

            start_time = asyncio.get_event_loop().time()
            all_traces = []

            try:
                # Run agents concurrently
                results = await asyncio.wait_for(
                    asyncio.gather(
                        agent_a.run_async(task_a),
                        agent_b.run_async(task_b),
                        return_exceptions=True,
                    ),
                    timeout=60.0,
                )

                result_a, result_b = results
                execution_time = asyncio.get_event_loop().time() - start_time

                # Check that both agents completed their tasks successfully
                agent_a_success = all(
                    word in str(result_a).lower() for word in ["secret_a", "agent a secret data"]
                )
                agent_b_success = all(
                    word in str(result_b).lower() for word in ["secret_b", "agent b secret data"]
                )

                # Check that agents don't see each other's files in their responses
                cross_contamination_a = (
                    "agent b" in str(result_a).lower() or "secret_b" in str(result_a).lower()
                )
                cross_contamination_b = (
                    "agent a" in str(result_b).lower() or "secret_a" in str(result_b).lower()
                )

                isolation_maintained = not cross_contamination_a and not cross_contamination_b

                isolation_checks = [
                    agent_a_success,
                    agent_b_success,
                    isolation_maintained,
                ]

                isolation_score = sum(isolation_checks) / len(isolation_checks)
                passed = isolation_score >= 0.8 and execution_time < 45.0

                all_traces.append(
                    {
                        "agent_a_task": task_a,
                        "agent_b_task": task_b,
                        "agent_a_result": str(result_a)[:200] + "..."
                        if len(str(result_a)) > 200
                        else str(result_a),
                        "agent_b_result": str(result_b)[:200] + "..."
                        if len(str(result_b)) > 200
                        else str(result_b),
                        "execution_time": execution_time,
                        "isolation_maintained": isolation_maintained,
                    }
                )

                return {
                    "name": self.name,
                    "passed": passed,
                    "score": isolation_score,
                    "duration": execution_time,
                    "traces": all_traces,
                    "metadata": {
                        "agent_a_success": agent_a_success,
                        "agent_b_success": agent_b_success,
                        "isolation_maintained": isolation_maintained,
                        "cross_contamination_a": cross_contamination_a,
                        "cross_contamination_b": cross_contamination_b,
                        "execution_time": execution_time,
                    },
                }

            except asyncio.TimeoutError:
                execution_time = asyncio.get_event_loop().time() - start_time
                return {
                    "name": self.name,
                    "passed": False,
                    "score": 0.0,
                    "duration": execution_time,
                    "error": "Timeout during workspace isolation test",
                }
