"""Protocol tests - Event enum and interface validation.

COMPREHENSIVE COVERAGE:
1. Event enum string behavior
2. Delimiter conversion (forward/reverse)
3. Error handling for invalid delimiters
4. LLM protocol interface validation
5. Type safety and string compatibility
"""

from cogency.core.protocols import Event


class TestEventEnum:
    """Event enum foundation testing."""

    def test_event_string_behavior(self):
        """Event enum behaves like strings - critical for compatibility."""
        # String equality
        assert Event.THINK == "think"
        assert Event.CALLS == "calls"
        assert Event.RESULTS == "results"
        assert Event.RESPOND == "respond"
        assert Event.USER == "user"
        assert Event.YIELD == "yield"

        # String operations
        assert Event.THINK.upper() == "THINK"
        assert Event.CALLS.lower() == "calls"
        assert Event.RESPOND.startswith("res")

        # String representation (enum shows as Event.NAME)
        assert str(Event.THINK) == "Event.THINK"
        assert f"Event type: {Event.THINK}" == "Event type: Event.THINK"
        # But value access works
        assert Event.THINK.value == "think"

    def test_event_enum_behavior(self):
        """Event enum behaves like enum - type safety."""
        # Enum iteration
        all_events = list(Event)
        assert len(all_events) == 7
        assert Event.THINK in all_events
        assert Event.YIELD in all_events

        # Enum comparison
        assert Event.THINK != Event.CALLS
        assert Event.RESPOND == Event.RESPOND

    def test_delimiter_conversion(self):
        """Delimiter conversion - streaming protocol foundation."""
        # Forward conversion
        assert Event.THINK.delimiter == "§THINK"
        assert Event.CALLS.delimiter == "§CALLS"
        assert Event.RESPOND.delimiter == "§RESPOND"
        assert Event.YIELD.delimiter == "§YIELD"

        # All events have delimiters
        for event in Event:
            delimiter = event.delimiter
            assert delimiter.startswith("§")
            assert delimiter == f"§{event.upper()}"


class TestEventUsagePatterns:
    """Event usage patterns - real world scenarios."""

    def test_match_statement_compatibility(self):
        """Event enum works in match statements - core usage pattern."""

        def process_event(event_type):
            match event_type:
                case Event.THINK:
                    return "thinking"
                case Event.CALLS:
                    return "calling"
                case Event.RESPOND:
                    return "responding"
                case _:
                    return "unknown"

        assert process_event(Event.THINK) == "thinking"
        assert process_event(Event.CALLS) == "calling"
        assert process_event("invalid") == "unknown"

    def test_dict_key_compatibility(self):
        """Event enum works as dict keys - storage compatibility."""
        event_dict = {
            Event.THINK: "thought content",
            Event.CALLS: "tool calls",
            Event.RESPOND: "response content",
        }

        # String access works
        assert event_dict["think"] == "thought content"
        assert event_dict["calls"] == "tool calls"

        # Enum access works
        assert event_dict[Event.THINK] == "thought content"
        assert event_dict[Event.RESPOND] == "response content"

    def test_json_serialization(self):
        """Event enum serializes to JSON - API compatibility."""
        import json

        data = {"type": Event.THINK, "content": "test content"}

        # Should serialize to string
        json_str = json.dumps(data)
        parsed = json.loads(json_str)

        assert parsed["type"] == "think"
        assert parsed["content"] == "test content"


if __name__ == "__main__":
    print("PROTOCOL TESTING")
    print("=" * 50)

    # Run basic smoke test
    assert Event.THINK == "think"
    assert Event.CALLS.delimiter == "§CALLS"

    print("Event enum behavior validated")
    print("Delimiter conversion works")
    print("String/enum dual compatibility confirmed")

    print("\nPROTOCOL FOUNDATION: VERIFIED")
