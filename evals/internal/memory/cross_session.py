"""Cross-session memory dependency benchmark."""

import asyncio
from typing import Any

from .base import MemoryBenchmark


class CrossSessionMemory(MemoryBenchmark):
    """Test memory persistence across completely separate agent sessions.

    This benchmark simulates real-world usage where agents must recall
    information from previous conversations after context clearing.
    """

    name = "cross_session_memory"
    description = "Cross-session dependency test with context clearing"

    async def run_benchmark(self) -> dict[str, Any]:
        """Execute cross-session memory evaluation."""

        test_scenarios = [
            {
                "name": "project_continuity",
                "sessions": [
                    [
                        "I'm starting Project Phoenix. The API endpoint is https://api.phoenix.dev and the auth token is px_abc123. Please remember these details."
                    ],
                    ["What was the API endpoint for Project Phoenix?"],
                    [
                        "I need to continue working on Project Phoenix. What authentication details do you have stored?"
                    ],
                ],
                "expected_recalls": [
                    "Acknowledgment of storing Project Phoenix details",
                    "https://api.phoenix.dev",
                    "Auth token px_abc123",
                ],
            },
            {
                "name": "user_preferences",
                "sessions": [
                    [
                        "My preferences: I prefer TypeScript over JavaScript, use tabs not spaces, and deploy to AWS us-east-1. Store this profile."
                    ],
                    ["What's my preferred cloud region?"],
                    ["Set up a new project using my coding preferences."],
                ],
                "expected_recalls": [
                    "Confirmation of storing user preferences",
                    "AWS us-east-1",
                    "TypeScript, tabs, AWS us-east-1",
                ],
            },
            {
                "name": "learning_retention",
                "sessions": [
                    [
                        "I learned that Redis persistence uses RDB snapshots and AOF logs. The default port is 6379. Remember this for future discussions."
                    ],
                    ["What's the default Redis port?"],
                    ["Explain Redis persistence methods we discussed."],
                ],
                "expected_recalls": [
                    "Acknowledgment of storing Redis information",
                    "6379",
                    "RDB snapshots and AOF logs",
                ],
            },
        ]

        results = []

        for scenario in test_scenarios:
            scenario_results = await self._run_scenario(scenario)
            results.append(scenario_results)

            # Brief pause between scenarios to ensure session isolation
            await asyncio.sleep(1)

        # Calculate overall performance
        total_sessions = sum(len(r["session_results"]) for r in results)
        successful_recalls = sum(
            sum(1 for sr in r["session_results"] if sr["judge_result"]["score"]["value"] >= 7.0)
            for r in results
        )

        success_rate = successful_recalls / total_sessions if total_sessions > 0 else 0.0

        return {
            "name": self.name,
            "description": self.description,
            "scenarios": results,
            "summary": {
                "total_scenarios": len(test_scenarios),
                "total_sessions": total_sessions,
                "successful_recalls": successful_recalls,
                "success_rate": round(success_rate, 3),
                "benchmark_passed": success_rate >= 0.7,  # 70% threshold
            },
            "evaluation_focus": "Cross-session memory with forced context clearing",
        }

    async def _run_scenario(self, scenario: dict[str, Any]) -> dict[str, Any]:
        """Run a single memory scenario with multiple sessions."""

        user_id = f"test_user_{scenario['name']}"
        session_results = []

        for i, (session_actions, expected_recall) in enumerate(
            zip(scenario["sessions"], scenario["expected_recalls"])
        ):
            # Force context clearing by creating new agent instance
            session = await self.execute_session(
                session_id=f"{scenario['name']}_session_{i}",
                actions=session_actions,
                user_id=user_id,
                context_clear=True,  # Critical: forces new agent instance
            )

            # Evaluate memory quality
            response = session.responses[0]  # Single action per session in this test
            judge_result = await self.evaluate_memory_quality(
                test_case=session_actions[0],
                expected_recall=expected_recall,
                actual_response=response,
                memory_type=f"cross_session_{scenario['name']}",
            )

            # Log result
            self.logger.log_result(
                eval_name=f"{self.name}_{scenario['name']}_session_{i}",
                judge_result=judge_result,
                agent_metadata={
                    "scenario": scenario["name"],
                    "session_index": i,
                    "user_id": user_id,
                    "context_cleared": True,
                    "session_id": session.session_id,
                },
                execution_time=1.0,  # Placeholder
            )

            session_results.append(
                {
                    "session_index": i,
                    "action": session_actions[0],
                    "expected_recall": expected_recall,
                    "agent_response": response,
                    "judge_result": {
                        "score": {
                            "value": judge_result.score.value,
                            "confidence": judge_result.score.confidence,
                        },
                        "reasoning": judge_result.score.reasoning,
                    },
                    "memory_demonstrated": judge_result.score.value >= 7.0,
                }
            )

        return {
            "scenario_name": scenario["name"],
            "session_results": session_results,
            "scenario_success": all(sr["memory_demonstrated"] for sr in session_results),
        }
