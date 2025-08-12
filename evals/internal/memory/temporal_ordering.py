"""Temporal ordering memory benchmark."""

import asyncio
from typing import Any

from .base import MemoryBenchmark


class TemporalOrdering(MemoryBenchmark):
    """Test agent's ability to maintain temporal ordering of information.

    Challenges agent to recall when specific information was learned
    and maintain chronological understanding across sessions.
    """

    name = "temporal_ordering"
    description = "Temporal memory ordering with chronological recall"

    async def run_benchmark(self) -> dict[str, Any]:
        """Execute temporal ordering evaluation."""

        # Simulate information learned over "time" (separate sessions)
        temporal_scenarios = [
            {
                "name": "feature_development_timeline",
                "timeline": [
                    ("day_1", "Started working on authentication feature. Using JWT tokens."),
                    ("day_2", "Added database integration. Using PostgreSQL with users table."),
                    ("day_3", "Implemented rate limiting. Using Redis for session storage."),
                    ("day_4", "Added API documentation. Using OpenAPI/Swagger format."),
                ],
                "temporal_queries": [
                    ("What did we work on day 1?", "authentication feature, JWT tokens"),
                    ("What database did we choose on day 2?", "PostgreSQL"),
                    (
                        "What was added after database integration but before documentation?",
                        "rate limiting, Redis",
                    ),
                    (
                        "In what order did we implement: documentation, auth, database, rate limiting?",
                        "auth (day 1), database (day 2), rate limiting (day 3), documentation (day 4)",
                    ),
                ],
            },
            {
                "name": "learning_progression",
                "timeline": [
                    ("week_1", "Learned React basics: components, props, state management."),
                    ("week_2", "Studied React hooks: useState, useEffect, custom hooks."),
                    ("week_3", "Explored state management: Redux, context API, Zustand."),
                    ("week_4", "Advanced patterns: render props, higher-order components."),
                ],
                "temporal_queries": [
                    ("What did I learn in week 2?", "React hooks, useState, useEffect"),
                    (
                        "What came after hooks but before advanced patterns?",
                        "state management, Redux",
                    ),
                    (
                        "What were the first React concepts I learned?",
                        "components, props, state management",
                    ),
                    (
                        "List my learning progression in chronological order",
                        "week 1: React basics, week 2: hooks, week 3: state management, week 4: advanced patterns",
                    ),
                ],
            },
        ]

        results = []

        for scenario in temporal_scenarios:
            scenario_results = await self._run_temporal_scenario(scenario)
            results.append(scenario_results)

            await asyncio.sleep(1)  # Session isolation pause

        # Calculate temporal accuracy
        total_queries = sum(len(r["query_results"]) for r in results)
        accurate_temporal_recalls = sum(
            sum(1 for qr in r["query_results"] if qr["temporal_accuracy"] >= 7.0) for r in results
        )

        temporal_accuracy = accurate_temporal_recalls / total_queries if total_queries > 0 else 0.0

        return {
            "name": self.name,
            "description": self.description,
            "scenarios": results,
            "summary": {
                "total_scenarios": len(temporal_scenarios),
                "total_queries": total_queries,
                "accurate_temporal_recalls": accurate_temporal_recalls,
                "temporal_accuracy": round(temporal_accuracy, 3),
                "benchmark_passed": temporal_accuracy
                >= 0.6,  # 60% threshold (harder than basic recall)
            },
            "evaluation_focus": "Temporal ordering and chronological memory",
        }

    async def _run_temporal_scenario(self, scenario: dict[str, Any]) -> dict[str, Any]:
        """Run temporal memory scenario."""

        user_id = f"temporal_user_{scenario['name']}"

        # Phase 1: Learn information over "time" (separate sessions)
        for time_point, information in scenario["timeline"]:
            await self.execute_session(
                session_id=f"{scenario['name']}_{time_point}",
                actions=[f"Remember this for {time_point}: {information}"],
                user_id=user_id,
                context_clear=True,
            )

            # Small delay to simulate temporal separation
            await asyncio.sleep(0.5)

        # Phase 2: Test temporal recall
        query_results = []

        for query, expected_temporal_info in scenario["temporal_queries"]:
            # Fresh session for each query to test memory system
            recall_session = await self.execute_session(
                session_id=f"{scenario['name']}_query_{len(query_results)}",
                actions=[query],
                user_id=user_id,
                context_clear=True,
            )

            response = recall_session.responses[0]

            # Evaluate temporal accuracy
            judge_result = await self.evaluate_temporal_accuracy(
                query=query,
                expected_temporal_info=expected_temporal_info,
                actual_response=response,
                scenario_name=scenario["name"],
            )

            self.logger.log_result(
                eval_name=f"{self.name}_{scenario['name']}_query_{len(query_results)}",
                judge_result=judge_result,
                agent_metadata={
                    "scenario": scenario["name"],
                    "query_type": "temporal_recall",
                    "expected_info": expected_temporal_info,
                    "user_id": user_id,
                },
                execution_time=1.0,
            )

            query_results.append(
                {
                    "query": query,
                    "expected_temporal_info": expected_temporal_info,
                    "agent_response": response,
                    "temporal_accuracy": judge_result.score.value,
                    "judge_confidence": judge_result.score.confidence,
                    "judge_reasoning": judge_result.score.reasoning,
                }
            )

        return {
            "scenario_name": scenario["name"],
            "timeline": scenario["timeline"],
            "query_results": query_results,
            "scenario_temporal_accuracy": sum(qr["temporal_accuracy"] for qr in query_results)
            / len(query_results),
        }

    async def evaluate_temporal_accuracy(
        self, query: str, expected_temporal_info: str, actual_response: str, scenario_name: str
    ) -> Any:
        """Evaluate temporal memory accuracy."""

        criteria = f"""Temporal Memory Assessment:

Query: {query}
Expected Temporal Information: {expected_temporal_info}

Rate the agent's temporal memory accuracy:

1. Does the response contain the correct temporal information?
2. Does it demonstrate understanding of chronological order?
3. Are specific time references (day 1, week 2, etc.) accurate?
4. Does it show genuine memory of the learning sequence?

Score 1-3: No temporal awareness or incorrect chronology
Score 4-6: Partial temporal memory with some correct sequences
Score 7-8: Good temporal memory with mostly correct chronology
Score 9-10: Perfect temporal memory with precise chronological details"""

        return await self.judge.evaluate(
            agent_response=actual_response,
            test_case=query,
            criteria=criteria,
            context={
                "scenario": scenario_name,
                "evaluation_type": "temporal_ordering",
                "expected_temporal_info": expected_temporal_info,
            },
        )
