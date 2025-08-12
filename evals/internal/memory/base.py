"""Base class for memory benchmarks with hack-resistant design."""

import tempfile
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cogency import Agent

from ...judges.claude_judge import ClaudeJudge
from ...judges.scoring import JudgeResult
from ...logging import EvalLogger


@dataclass
class MemorySession:
    """Single memory session with context isolation."""

    session_id: str
    user_id: str
    agent: Agent
    actions: list[str]
    responses: list[str]
    timestamp: float


class MemoryBenchmark(ABC):
    """Base class for sophisticated memory evaluations."""

    name: str = "memory_base"
    description: str = "Base memory benchmark"

    def __init__(self):
        self.judge = ClaudeJudge()
        self.logger = EvalLogger()
        self.temp_dir = None
        self.sessions: list[MemorySession] = []

    def setup_isolated_environment(self) -> Path:
        """Create isolated memory environment."""
        self.temp_dir = tempfile.mkdtemp(prefix="memory_eval_")
        return Path(self.temp_dir)

    def cleanup_environment(self):
        """Clean up isolated environment."""
        if self.temp_dir:
            import shutil

            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_agent(self, session_id: str, user_id: str = None) -> Agent:
        """Create agent with persistent memory in isolated environment."""
        # Force new agent instance with isolated memory store
        return Agent(
            role=f"memory_test_agent_{session_id}", memory=True, observe=True, max_iterations=8
        )

    async def execute_session(
        self, session_id: str, actions: list[str], user_id: str = None, context_clear: bool = True
    ) -> MemorySession:
        """Execute a memory session with optional context clearing."""

        user_id = user_id or f"test_user_{session_id}"
        agent = self.create_agent(session_id, user_id)
        responses = []

        for action in actions:
            # Context clearing between actions if requested
            if context_clear and len(responses) > 0:
                # Create fresh agent instance to simulate new session
                agent = self.create_agent(f"{session_id}_{len(responses)}", user_id)

            response = await agent.run_async(action, user_id=user_id)
            responses.append(response)

        session = MemorySession(
            session_id=session_id,
            user_id=user_id,
            agent=agent,
            actions=actions,
            responses=responses,
            timestamp=time.time(),
        )

        self.sessions.append(session)
        return session

    async def evaluate_memory_quality(
        self, test_case: str, expected_recall: str, actual_response: str, memory_type: str
    ) -> JudgeResult:
        """Evaluate memory recall quality using Claude judge."""

        criteria = f"""Memory Quality Assessment for {memory_type}:

Expected Information to Recall: {expected_recall}

Rate the agent's ability to:
1. Accurately recall previously stored information
2. Maintain context across session boundaries
3. Demonstrate genuine memory persistence (not context hacking)
4. Provide specific details from previous interactions

Score 1-3: No memory demonstrated or hallucinated information
Score 4-6: Partial memory with some correct details
Score 7-8: Good memory with most details correct
Score 9-10: Perfect memory with all specific details intact"""

        return await self.judge.evaluate(
            agent_response=actual_response,
            test_case=test_case,
            criteria=criteria,
            context={
                "memory_type": memory_type,
                "expected_recall": expected_recall,
                "evaluation_focus": "cross_session_memory",
            },
        )

    @abstractmethod
    async def run_benchmark(self) -> dict[str, Any]:
        """Execute the specific memory benchmark."""
        pass

    async def execute(self) -> dict[str, Any]:
        """Execute benchmark with proper setup/teardown."""
        try:
            self.setup_isolated_environment()
            results = await self.run_benchmark()

            # Generate comprehensive report
            report = self.logger.generate_report()
            results["logging_report"] = report

            return results
        finally:
            self.cleanup_environment()
