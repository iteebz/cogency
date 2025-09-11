"""Protocol tests."""

import json

from cogency.core.protocols import Event


def test_event_protocol():
    """Event enum handles string equality, delimiters, dict keys, JSON serialization."""

    # String equality - core compatibility
    assert Event.THINK == "think"
    assert Event.CALLS == "calls"
    assert Event.RESPOND == "respond"
    assert Event.EXECUTE == "execute"

    # Delimiter conversion
    assert Event.THINK.delimiter == "§THINK"
    assert Event.CALLS.delimiter == "§CALLS"
    assert Event.RESPOND.delimiter == "§RESPOND"
    assert Event.EXECUTE.delimiter == "§EXECUTE"

    # Dict key compatibility (string and enum access)
    event_dict = {Event.THINK: "content"}
    assert event_dict["think"] == "content"
    assert event_dict[Event.THINK] == "content"

    # JSON serialization
    data = {"type": Event.THINK, "content": "test"}
    json_str = json.dumps(data)
    parsed = json.loads(json_str)
    assert parsed["type"] == "think"

    # Match statement compatibility
    def process_event(event_type):
        match event_type:
            case Event.THINK:
                return "thinking"
            case Event.CALLS:
                return "calling"
            case _:
                return "unknown"

    assert process_event(Event.THINK) == "thinking"
    assert process_event("invalid") == "unknown"
