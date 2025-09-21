"""Minimal integration test - streaming flow verification.

Tests core Parser→Accumulator→Executor pipeline to ensure protocol tokens
correctly flow through the complete streaming architecture.
"""

import pytest

from cogency.core.accumulator import Accumulator
from cogency.core.parser import parse_tokens


@pytest.mark.asyncio
async def test_parser_accumulator_executor_flow(mock_llm, mock_config, mock_tool):
    """Parser→Accumulator→Executor integration."""

    # Set up streaming protocol
    mock_llm.set_response_tokens(
        [
            "§think: I need to call a tool.\n",
            '§call: {"name": "test_tool", "args": {"message": "hello world"}}\n',
            "§execute\n",
            "§respond: The tool completed successfully.\n",
            "§end\n",
        ]
    )

    # Create config with mock_tool
    from cogency.core.config import Config, Security

    config = Config(
        llm=mock_config.llm, storage=mock_config.storage, tools=[mock_tool], security=Security(sandbox=True)
    )

    # Parse tokens directly
    parser_events = parse_tokens(mock_llm.stream([]))

    # Process through accumulator
    accumulator = Accumulator(config, "test_user", "test_conv", chunks=False)
    events = []

    async for event in accumulator.process(parser_events):
        events.append(event)

    # Validation - semantic events only
    assert len(events) > 0

    event_types = [e["type"] for e in events]
    assert "think" in event_types
    assert "result" in event_types  # Tool execution result
    assert "end" in event_types
