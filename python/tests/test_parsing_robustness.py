
import pytest

from cogency.utils.parsing import parse_plan_response, parse_reflect_response


class TestPlanResponseParsing:
    """Test robustness of plan response parsing."""

    def test_valid_json_tool_needed(self):
        """Test valid JSON with tool_needed action."""
        response = '{"action": "tool_needed", "reasoning": "Math calculation required", "strategy": "Use calculator"}'
        route, data = parse_plan_response(response)
        assert route == "reason"
        assert data["action"] == "tool_needed"

    def test_valid_json_direct_response(self):
        """Test valid JSON with direct_response action."""
        response = '{"action": "direct_response", "reasoning": "General knowledge", "answer": "Hello"}'
        route, data = parse_plan_response(response)
        assert route == "respond"
        assert data["action"] == "direct_response"

    def test_malformed_json(self):
        """Test malformed JSON falls back gracefully."""
        response = '{"action": "tool_needed", "reasoning": "Math calculation", missing closing brace'
        route, data = parse_plan_response(response)
        assert route == "respond"  # fallback
        assert data["action"] == "direct_response"

    def test_non_json_with_tool_needed_prefix(self):
        """Test non-JSON with TOOL_NEEDED prefix."""
        response = "TOOL_NEEDED: Calculator required for math"
        route, data = parse_plan_response(response)
        assert route == "reason"
        assert data["action"] == "tool_needed"

    def test_plain_text_reasoning(self):
        """Test plain text response with reasoning."""
        response = "Reasoning: This is a simple greeting"
        route, data = parse_plan_response(response)
        assert route == "respond"
        assert data["action"] == "direct_response"

    def test_empty_response(self):
        """Test empty response."""
        response = ""
        route, data = parse_plan_response(response)
        assert route == "respond"
        assert data["action"] == "direct_response"


class TestReflectResponseParsing:
    """Test robustness of reflect response parsing."""

    def test_valid_json_complete(self):
        """Test valid JSON with complete status."""
        response = '{"status": "complete", "assessment": "Task finished successfully"}'
        route, data = parse_reflect_response(response)
        assert route == "respond"
        assert data["status"] == "complete"

    def test_valid_json_continue(self):
        """Test valid JSON with continue status."""
        response = '{"status": "continue", "reasoning": "More work needed"}'
        route, data = parse_reflect_response(response)
        assert route == "reason"
        assert data["status"] == "continue"

    def test_malformed_json(self):
        """Test malformed JSON defaults to complete."""
        response = '{"status": "complete", "assessment": "Task finished", missing brace'
        route, data = parse_reflect_response(response)
        assert route == "respond"  # defaults to complete
        assert data["status"] == "complete"

    def test_unknown_status(self):
        """Test unknown status defaults to complete."""
        response = '{"status": "unknown", "message": "Something happened"}'
        route, data = parse_reflect_response(response)
        assert route == "respond"
        assert data["status"] == "complete"

    def test_task_complete_prefix(self):
        """Test TASK_COMPLETE prefix."""
        response = "TASK_COMPLETE: All work finished"
        route, data = parse_reflect_response(response)
        assert route == "respond"
        assert data["status"] == "complete"

    def test_plain_text_defaults_complete(self):
        """Test plain text defaults to complete to prevent loops."""
        response = "The task was completed successfully"
        route, data = parse_reflect_response(response)
        assert route == "respond"
        assert data["status"] == "complete"


class TestErrorHandling:
    """Test error handling edge cases."""

    def test_none_input(self):
        """Test None input handling."""
        route, data = parse_plan_response(None)
        assert route == "respond"
        assert data["action"] == "direct_response"

    def test_very_long_response(self):
        """Test very long response handling."""
        long_response = "Reasoning: " + "A" * 10000
        route, data = parse_plan_response(long_response)
        assert route == "respond"
        assert "A" * 100 in data["content"]  # Should handle long content

    def test_unicode_characters(self):
        """Test unicode character handling."""
        response = '{"action": "direct_response", "reasoning": "Unicode test: 🤖🔧📁", "answer": "Hello 世界"}'
        route, data = parse_plan_response(response)
        assert route == "respond"
        assert "🤖" in data["reasoning"]


if __name__ == "__main__":
    pytest.main([__file__])
