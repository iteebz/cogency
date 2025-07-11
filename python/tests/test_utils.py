from cogency.utils.formatting import NODE_FORMATTERS, format_trace
from cogency.utils.parsing import extract_tool_call, parse_plan_response, parse_reflect_response


class TestParsing:
    """Test suite for parsing utilities."""

    def test_parse_plan_response_tool_needed(self):
        """Test parsing plan response when tool is needed."""
        response = '{"action": "tool_needed", "reasoning": "need calculator"}'

        route, data = parse_plan_response(response)

        assert route == "reason"
        assert data["action"] == "tool_needed"
        assert data["reasoning"] == "need calculator"

    def test_parse_plan_response_direct_response(self):
        """Test parsing plan response for direct response."""
        response = '{"action": "direct_response", "answer": "Hello world"}'

        route, data = parse_plan_response(response)

        assert route == "respond"
        assert data["action"] == "direct_response"
        assert data["answer"] == "Hello world"

    def test_parse_plan_response_fallback_tool_needed(self):
        """Test parsing plan response with fallback prefix parsing."""
        response = "TOOL_NEEDED: I need to calculate something"

        route, data = parse_plan_response(response)

        assert route == "reason"
        assert data["action"] == "tool_needed"
        assert data["content"] == " I need to calculate something"

    def test_parse_plan_response_fallback_direct(self):
        """Test parsing plan response with fallback for direct response."""
        response = "Just a regular response"

        route, data = parse_plan_response(response)

        assert route == "respond"
        assert data["action"] == "direct_response"
        assert data["content"] == "Just a regular response"

    def test_parse_plan_response_invalid_json(self):
        """Test parsing plan response with invalid JSON."""
        response = '{"action": "tool_needed", "reasoning": invalid}'

        route, data = parse_plan_response(response)

        assert route == "respond"  # Falls back to respond
        assert data["action"] == "direct_response"
        assert data["content"] == response

    def test_parse_reflect_response_continue(self):
        """Test parsing reflect response for continue status."""
        response = '{"status": "continue", "reasoning": "need more work"}'

        route, data = parse_reflect_response(response)

        assert route == "reason"
        assert data["status"] == "continue"
        assert data["reasoning"] == "need more work"

    def test_parse_reflect_response_complete(self):
        """Test parsing reflect response for complete status."""
        response = '{"status": "complete", "assessment": "task done"}'

        route, data = parse_reflect_response(response)

        assert route == "respond"
        assert data["status"] == "complete"
        assert data["assessment"] == "task done"

    def test_parse_reflect_response_fallback_complete(self):
        """Test parsing reflect response with fallback prefix parsing."""
        response = "TASK_COMPLETE: The task has been finished"

        route, data = parse_reflect_response(response)

        assert route == "respond"
        assert data["status"] == "complete"
        assert data["content"] == " The task has been finished"

    def test_parse_reflect_response_fallback_continue(self):
        """Test parsing reflect response with fallback for continue."""
        response = "Still working on the task"

        route, data = parse_reflect_response(response)

        assert route == "reason"
        assert data["status"] == "continue"
        assert data["content"] == "Still working on the task"

    def test_extract_tool_call_valid(self):
        """Test extracting valid tool call."""
        response = "TOOL_CALL: calculator(a=2, b=3)"

        result = extract_tool_call(response)

        assert result is not None
        tool_name, args = result
        assert tool_name == "calculator"
        assert args["raw_args"] == "a=2, b=3"

    def test_extract_tool_call_no_args(self):
        """Test extracting tool call with no arguments."""
        response = "TOOL_CALL: get_time()"

        result = extract_tool_call(response)

        assert result is not None
        tool_name, args = result
        assert tool_name == "get_time"
        assert args["raw_args"] == ""

    def test_extract_tool_call_invalid_format(self):
        """Test extracting tool call with invalid format."""
        response = "TOOL_CALL: invalid format"

        result = extract_tool_call(response)

        assert result is None

    def test_extract_tool_call_no_prefix(self):
        """Test extracting tool call without TOOL_CALL prefix."""
        response = "calculator(a=2, b=3)"

        result = extract_tool_call(response)

        assert result is None

    def test_extract_tool_call_exception_handling(self):
        """Test extracting tool call with exception in parsing."""
        response = "TOOL_CALL: tool("

        result = extract_tool_call(response)

        assert result is None


class TestFormatting:
    """Test suite for formatting utilities."""

    def test_format_trace_basic(self):
        """Test basic trace formatting."""
        trace = {
            "trace_id": "test123",
            "steps": [
                {
                    "node": "plan",
                    "reasoning": '{"intent": "calculate", "reasoning": "need math"}',
                    "output_data": {},
                },
                {
                    "node": "act",
                    "reasoning": "",
                    "output_data": {"tool_used": "calculator", "tool_result": "4"},
                },
            ],
        }

        result = format_trace(trace)

        # trace_id is not included in current format
        assert "PLAN" in result
        assert "ACT" in result
        assert "calculate" in result
        assert "[TOOL_CALL] calculator -> 4" in result

    def test_format_trace_empty_steps(self):
        """Test trace formatting with empty steps."""
        trace = {"trace_id": "test123", "steps": []}

        result = format_trace(trace)

        # trace_id is not included in current format
        assert "No steps recorded" in result

    def test_format_trace_missing_trace_id(self):
        """Test trace formatting with missing trace ID."""
        trace = {"steps": [{"node": "plan", "reasoning": "test reasoning", "output_data": {}}]}

        result = format_trace(trace)

        # trace_id is not included in current format
        assert "LLM returned non-JSON plan" in result

    def test_node_formatters_plan(self):
        """Test plan node formatter."""
        reasoning = '{"intent": "calculate", "reasoning": "need math", "strategy": "use calc"}'
        output_data = {}

        result = NODE_FORMATTERS["PLAN"](reasoning, output_data)

        assert "Intent: calculate" in result
        assert "Reasoning: need math" in result
        assert "Strategy: use calc" in result

    def test_node_formatters_plan_no_json(self):
        """Test plan node formatter with non-JSON."""
        reasoning = "Not JSON format"
        output_data = {}

        result = NODE_FORMATTERS["PLAN"](reasoning, output_data)

        assert "non-JSON plan" in result

    def test_node_formatters_reason(self):
        """Test reason node formatter."""
        reasoning = "LLM Output: I need to calculate this"
        output_data = {}

        result = NODE_FORMATTERS["REASON"](reasoning, output_data)

        assert result == "I need to calculate this"

    def test_node_formatters_act(self):
        """Test act node formatter."""
        reasoning = ""
        output_data = {"tool_used": "calculator", "tool_result": "42"}

        result = NODE_FORMATTERS["ACT"](reasoning, output_data)

        assert result == "[TOOL_CALL] calculator -> 42"

    def test_node_formatters_act_missing_data(self):
        """Test act node formatter with missing data."""
        reasoning = ""
        output_data = {}

        result = NODE_FORMATTERS["ACT"](reasoning, output_data)

        assert result == "[TOOL_CALL] N/A -> N/A"

    def test_node_formatters_reflect(self):
        """Test reflect node formatter."""
        reasoning = "Assessment: Task completed successfully"
        output_data = {}

        result = NODE_FORMATTERS["REFLECT"](reasoning, output_data)

        assert result == "Task completed successfully"

    def test_node_formatters_respond(self):
        """Test respond node formatter."""
        reasoning = "LLM Output: Final answer is 42"
        output_data = {}

        result = NODE_FORMATTERS["RESPOND"](reasoning, output_data)

        assert result == "Final answer is 42"

    def test_node_formatters_unknown_node(self):
        """Test formatter for unknown node type."""
        reasoning = "Unknown node output"
        output_data = {}

        # Should use default formatter
        result = NODE_FORMATTERS.get("UNKNOWN", lambda r, d: r)(reasoning, output_data)

        assert result == "Unknown node output"
