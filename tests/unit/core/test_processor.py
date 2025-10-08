from unittest.mock import MagicMock

import pytest

from cogency.core.config import Config
from cogency.core.processor import _process_stream_event
from cogency.core.protocols import LLM, Storage
from cogency.lib import telemetry
from cogency.lib.metrics import Metrics


class MockStreamContext:
    def __init__(self):
        self.llm = MagicMock(spec=LLM)
        self.storage = MagicMock(spec=Storage)
        self.config = Config(llm=self.llm, storage=self.storage, tools=[])
        self.metrics = Metrics.init("test_model")
        self.telemetry_events = []
        self.complete = False
        self.conversation_id = "test_convo"


@pytest.fixture
def mock_context():
    context = MockStreamContext()
    context.metrics = MagicMock(spec=Metrics)
    context.metrics.event.return_value = {"type": "metrics", "data": {}}
    telemetry.add_event = MagicMock()
    return context


@pytest.mark.asyncio
async def test_process_stream_event_think(mock_context):
    event = {"type": "think", "content": "Thinking about the problem"}

    await _process_stream_event(mock_context, event)

    telemetry.add_event.assert_called_once_with(mock_context.telemetry_events, event)
    mock_context.metrics.add_output.assert_called_once_with(event["content"])
    assert not mock_context.complete


@pytest.mark.asyncio
async def test_process_stream_event_end(mock_context):
    event = {"type": "end"}

    await _process_stream_event(mock_context, event)

    telemetry.add_event.assert_called_once_with(mock_context.telemetry_events, event)
    assert mock_context.complete
