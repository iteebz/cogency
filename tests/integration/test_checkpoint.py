"""Smoke test: Checkpoint resume with Result pattern."""

import asyncio
import json
import os
import tempfile
from unittest.mock import AsyncMock

import pytest
from resilient_result import Result

from cogency.providers import LLM


class MockCheckpointLLM(LLM):
    """Mock LLM that simulates checkpoint/resume behavior."""

    def __init__(self):
        self.call_count = 0
        # Skip parent init to avoid API key requirements
        self.provider_name = "mock"
        self.enable_cache = False
        self._cache = None

    @property
    def default_model(self) -> str:
        return "mock-model"

    def _get_client(self):
        return None

    async def _run_impl(self, messages, **kwargs) -> str:
        self.call_count += 1
        content = messages[-1]["content"]
        last_msg = content.lower()

        # Check if this is a preparing request (looking for JSON format in prompt)
        if "json" in last_msg and ("format" in last_msg or "response" in last_msg):
            # Return valid JSON for preparing
            return """{"memory": null, "tags": null, "memory_type": "fact", "mode": "fast", "selected_tools": [], "reasoning": "Simple analysis task, no tools needed"}"""

        if "checkpoint" in last_msg and "resume" in last_msg:
            # Resuming from checkpoint
            return "Resuming from checkpoint. I was analyzing data and had completed steps 1-3. Now continuing with step 4: final analysis."

        elif self.call_count == 1:
            # Initial request - simulate long-running task
            return "I'll analyze this data in multiple steps. Step 1: Data validation complete. Creating checkpoint..."

        elif self.call_count == 2:
            # Second step after checkpoint
            return "Step 2: Data processing complete. Step 3: Intermediate analysis done. Ready for step 4."

        else:
            # Fallback for any other case
            return "Analysis complete."

    async def _stream_impl(self, messages, **kwargs):
        response = await self._run_impl(messages, **kwargs)
        for char in response:
            yield char

    async def run(self, messages, **kwargs):
        response = await self._run_impl(messages, **kwargs)
        return Result.ok(response)

    async def stream(self, messages, **kwargs):
        response = await self._run_impl(messages, **kwargs)
        yield response


class MockCheckpointAgent:
    """Agent with checkpoint/resume capabilities."""

    def __init__(self, llm=None, tools=None, depth=10, checkpoint_file=None, **kwargs):
        # Create agent with mock LLM
        from cogency import Agent

        # ServiceRegistry not needed for public API

        agent_kwargs = {"llm": llm or MockCheckpointLLM()}
        if tools:
            agent_kwargs["tools"] = tools

        self.agent = Agent(**agent_kwargs)
        self.checkpoint_file = checkpoint_file
        self.execution_state = {"step": 0, "completed_actions": [], "current_task": None}

    async def save_checkpoint(self):
        """Save current execution state to checkpoint file."""
        if self.checkpoint_file:
            try:
                checkpoint_data = {
                    "execution_state": self.execution_state,
                    "messages": self.messages if hasattr(self, "messages") else [],
                    "iteration": getattr(self, "iteration", 0),
                }

                with open(self.checkpoint_file, "w") as f:
                    json.dump(checkpoint_data, f, indent=2)

                return Result.ok(f"Checkpoint saved to {self.checkpoint_file}")

            except Exception as e:
                return Result.fail(f"Failed to save checkpoint: {str(e)}")

        return Result.fail("No checkpoint file specified")

    async def load_checkpoint(self):
        """Load execution state from checkpoint file."""
        if self.checkpoint_file and os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file) as f:
                    checkpoint_data = json.load(f)

                self.execution_state = checkpoint_data.get("execution_state", {})
                self.messages = checkpoint_data.get("messages", [])
                self.iteration = checkpoint_data.get("iteration", 0)

                return Result.ok("Checkpoint loaded successfully")

            except Exception as e:
                return Result.fail(f"Failed to load checkpoint: {str(e)}")

        return Result.fail("No checkpoint file found")

    async def run(self, prompt, resume_from_checkpoint=False):
        """Run agent with checkpoint support."""

        if resume_from_checkpoint:
            # Try to load from checkpoint
            load_result = await self.load_checkpoint()
            if load_result.success:
                # Add resume context to messages
                resume_prompt = f"You are resuming from a checkpoint. Previous context: {prompt}. Please continue from where you left off."
                result_string = await self.agent.run(resume_prompt)
                from resilient_result import Result

                return (
                    Result.ok(result_string)
                    if result_string and result_string.strip()
                    else Result.fail("Empty response")
                )

        # Normal execution with periodic checkpoints
        self.execution_state["current_task"] = prompt
        self.execution_state["step"] = 1

        # Simulate checkpoint during execution
        checkpoint_result = await self.save_checkpoint()
        if not checkpoint_result.success:
            return checkpoint_result

        # Run the actual task
        try:
            result_string = await self.agent.run(prompt)
            from resilient_result import Result

            if result_string is None:
                result = Result.fail("Agent returned None")
            elif not isinstance(result_string, str):
                result = Result.fail(f"Agent returned non-string: {type(result_string)}")
            elif not result_string.strip():
                result = Result.fail("Agent returned empty string")
            else:
                result = Result.ok(result_string)
        except Exception as e:
            import traceback

            from resilient_result import Result

            result = Result.fail(f"Agent execution failed: {str(e)}\n{traceback.format_exc()}")

        # Update execution state on completion
        if result.success:
            self.execution_state["step"] = 999  # Mark as completed
            self.execution_state["completed_actions"].append("task_completed")
            await self.save_checkpoint()

        return result


@pytest.mark.asyncio
async def test_resume():
    """Test agent can save checkpoints and resume from them."""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        checkpoint_file = f.name

    try:
        # Create agent with checkpoint support
        mock_llm = MockCheckpointLLM()
        agent = MockCheckpointAgent(
            llm=mock_llm, tools=[], checkpoint_file=checkpoint_file, depth=3
        )

        # Run initial task (will create checkpoint)
        initial_result = await agent.run("Analyze this complex dataset")
        assert initial_result.success, f"Initial run should succeed: {initial_result.error}"

        # Verify checkpoint file was created
        assert os.path.exists(checkpoint_file), "Checkpoint file should be created"

        # Create new agent instance to simulate restart
        new_agent = MockCheckpointAgent(
            llm=MockCheckpointLLM(), tools=[], checkpoint_file=checkpoint_file, depth=3
        )

        # Resume from checkpoint
        resume_result = await new_agent.run(
            "Analyze this complex dataset", resume_from_checkpoint=True
        )
        assert resume_result.success, f"Resume should succeed: {resume_result.error}"

        # Verify checkpoint was loaded
        load_result = await new_agent.load_checkpoint()
        assert load_result.success, "Should be able to load checkpoint"

        # Verify execution state was preserved
        assert new_agent.execution_state.get("current_task") == "Analyze this complex dataset"

    finally:
        # Cleanup
        if os.path.exists(checkpoint_file):
            os.unlink(checkpoint_file)


@pytest.mark.asyncio
async def test_failure_recovery():
    """Test checkpoint system handles failures gracefully."""

    # Test with invalid checkpoint file path
    agent = MockCheckpointAgent(
        llm=MockCheckpointLLM(),
        tools=[],
        checkpoint_file="/invalid/path/checkpoint.json",
        depth=2,
    )

    # Should handle checkpoint save failure gracefully
    save_result = await agent.save_checkpoint()
    assert not save_result.success, "Should fail to save to invalid path"
    assert (
        "no such file or directory" in save_result.error.lower()
        or "cannot find the path" in save_result.error.lower()
    )

    # Should handle checkpoint load failure gracefully
    load_result = await agent.load_checkpoint()
    assert not load_result.success, "Should fail to load from invalid path"


@pytest.mark.asyncio
async def test_data_integrity():
    """Test checkpoint data maintains integrity across save/load cycles."""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        checkpoint_file = f.name

    try:
        agent = MockCheckpointAgent(
            llm=MockCheckpointLLM(), tools=[], checkpoint_file=checkpoint_file, depth=2
        )

        # Set up complex execution state
        agent.execution_state = {
            "step": 42,
            "completed_actions": ["action1", "action2", "action3"],
            "current_task": "Complex multi-step analysis",
            "metadata": {"key": "value", "nested": {"data": [1, 2, 3]}},
        }

        # Save checkpoint
        save_result = await agent.save_checkpoint()
        assert save_result.success, "Should save checkpoint successfully"

        # Create new agent and load
        new_agent = MockCheckpointAgent(
            llm=MockCheckpointLLM(), tools=[], checkpoint_file=checkpoint_file, depth=2
        )

        load_result = await new_agent.load_checkpoint()
        assert load_result.success, "Should load checkpoint successfully"

        # Verify data integrity
        assert new_agent.execution_state["step"] == 42
        assert new_agent.execution_state["completed_actions"] == ["action1", "action2", "action3"]
        assert new_agent.execution_state["current_task"] == "Complex multi-step analysis"
        assert new_agent.execution_state["metadata"]["nested"]["data"] == [1, 2, 3]

    finally:
        if os.path.exists(checkpoint_file):
            os.unlink(checkpoint_file)


if __name__ == "__main__":
    asyncio.run(test_resume())
    print("✓ Checkpoint resume smoke test passed")
