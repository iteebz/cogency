"""Memory interference benchmark testing overlapping information."""

import asyncio
from typing import Any

from .base import MemoryBenchmark


class MemoryInterference(MemoryBenchmark):
    """Test agent's ability to maintain distinct memories under interference.

    Challenges agent with overlapping projects, similar contexts, and
    potential confusion scenarios to verify robust memory isolation.
    """

    name = "memory_interference"
    description = "Memory isolation under interference and confusion scenarios"

    async def run_benchmark(self) -> dict[str, Any]:
        """Execute memory interference evaluation."""

        interference_scenarios = [
            {
                "name": "similar_projects",
                "setup_phase": [
                    (
                        "project_alpha",
                        "Project Alpha: React frontend, Node.js backend, deployed on Heroku, uses MongoDB database, team lead: Sarah",
                    ),
                    (
                        "project_beta",
                        "Project Beta: React frontend, Node.js backend, deployed on AWS, uses PostgreSQL database, team lead: Michael",
                    ),
                    (
                        "project_gamma",
                        "Project Gamma: Vue.js frontend, Python backend, deployed on Heroku, uses Redis database, team lead: Sarah",
                    ),
                ],
                "interference_queries": [
                    ("Which project uses PostgreSQL?", "Project Beta"),
                    (
                        "What database does Sarah's project use?",
                        "Should distinguish between Alpha (MongoDB) and Gamma (Redis)",
                    ),
                    ("Which projects are deployed on Heroku?", "Project Alpha and Project Gamma"),
                    (
                        "What's the backend technology for the AWS-deployed project?",
                        "Node.js (Project Beta)",
                    ),
                ],
            },
            {
                "name": "user_confusion",
                "setup_phase": [
                    (
                        "user_a",
                        "User A preferences: Python, Django, PostgreSQL, prefers unit tests, works EST timezone",
                    ),
                    (
                        "user_b",
                        "User B preferences: Python, Flask, MongoDB, prefers integration tests, works PST timezone",
                    ),
                    (
                        "user_c",
                        "User C preferences: JavaScript, Express, PostgreSQL, prefers end-to-end tests, works EST timezone",
                    ),
                ],
                "interference_queries": [
                    ("Which user prefers Flask?", "User B"),
                    (
                        "What database do EST timezone users prefer?",
                        "Should distinguish: User A (PostgreSQL), User C (PostgreSQL)",
                    ),
                    ("Which Python user works in PST?", "User B"),
                    (
                        "What testing approach does the MongoDB user prefer?",
                        "Integration tests (User B)",
                    ),
                ],
            },
        ]

        results = []

        for scenario in interference_scenarios:
            scenario_results = await self._run_interference_scenario(scenario)
            results.append(scenario_results)

            await asyncio.sleep(1)

        # Calculate interference resistance
        total_queries = sum(len(r["query_results"]) for r in results)
        resistant_to_interference = sum(
            sum(1 for qr in r["query_results"] if qr["interference_resistance"] >= 7.0)
            for r in results
        )

        resistance_rate = resistant_to_interference / total_queries if total_queries > 0 else 0.0

        return {
            "name": self.name,
            "description": self.description,
            "scenarios": results,
            "summary": {
                "total_scenarios": len(interference_scenarios),
                "total_queries": total_queries,
                "resistant_to_interference": resistant_to_interference,
                "interference_resistance_rate": round(resistance_rate, 3),
                "benchmark_passed": resistance_rate >= 0.6,  # 60% threshold
            },
            "evaluation_focus": "Memory isolation under interference conditions",
        }

    async def _run_interference_scenario(self, scenario: dict[str, Any]) -> dict[str, Any]:
        """Run interference memory scenario."""

        user_id = f"interference_user_{scenario['name']}"

        # Phase 1: Establish overlapping/similar information across sessions
        for context_id, information in scenario["setup_phase"]:
            await self.execute_session(
                session_id=f"{scenario['name']}_{context_id}",
                actions=[f"Store this information about {context_id}: {information}"],
                user_id=user_id,
                context_clear=True,
            )

            # Brief pause between setups
            await asyncio.sleep(0.3)

        # Phase 2: Test memory isolation under interference
        query_results = []

        for query, expected_distinction in scenario["interference_queries"]:
            # Fresh session to test memory recall under potential confusion
            recall_session = await self.execute_session(
                session_id=f"{scenario['name']}_interference_query_{len(query_results)}",
                actions=[query],
                user_id=user_id,
                context_clear=True,
            )

            response = recall_session.responses[0]

            # Evaluate interference resistance
            judge_result = await self.evaluate_interference_resistance(
                query=query,
                expected_distinction=expected_distinction,
                actual_response=response,
                scenario_name=scenario["name"],
                setup_contexts=[ctx[0] for ctx in scenario["setup_phase"]],
            )

            self.logger.log_result(
                eval_name=f"{self.name}_{scenario['name']}_interference_{len(query_results)}",
                judge_result=judge_result,
                agent_metadata={
                    "scenario": scenario["name"],
                    "query_type": "interference_test",
                    "expected_distinction": expected_distinction,
                    "setup_contexts": [ctx[0] for ctx in scenario["setup_phase"]],
                    "user_id": user_id,
                },
                execution_time=1.0,
            )

            query_results.append(
                {
                    "query": query,
                    "expected_distinction": expected_distinction,
                    "agent_response": response,
                    "interference_resistance": judge_result.score.value,
                    "judge_confidence": judge_result.score.confidence,
                    "judge_reasoning": judge_result.score.reasoning,
                    "correctly_distinguished": judge_result.score.value >= 7.0,
                }
            )

        return {
            "scenario_name": scenario["name"],
            "setup_contexts": scenario["setup_phase"],
            "query_results": query_results,
            "interference_resistance_rate": sum(
                qr["interference_resistance"] for qr in query_results
            )
            / len(query_results),
        }

    async def evaluate_interference_resistance(
        self,
        query: str,
        expected_distinction: str,
        actual_response: str,
        scenario_name: str,
        setup_contexts: list,
    ) -> Any:
        """Evaluate memory's resistance to interference."""

        criteria = f"""Memory Interference Resistance Assessment:

Query: {query}
Expected Distinction: {expected_distinction}
Context Setup: {', '.join(setup_contexts)}

Rate the agent's ability to resist memory interference:

1. Does the response correctly distinguish between similar contexts?
2. Are specific details accurately attributed to the right entity?
3. Does it avoid confusion between overlapping information?
4. Does it demonstrate precise memory isolation?

Score 1-3: Significant confusion, wrong attributions, mixed up details
Score 4-6: Some correct distinctions but with confusion or ambiguity
Score 7-8: Good distinction with mostly correct attributions
Score 9-10: Perfect memory isolation with precise distinctions"""

        return await self.judge.evaluate(
            agent_response=actual_response,
            test_case=query,
            criteria=criteria,
            context={
                "scenario": scenario_name,
                "evaluation_type": "interference_resistance",
                "expected_distinction": expected_distinction,
                "setup_contexts": setup_contexts,
            },
        )
