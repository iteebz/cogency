"""Shared prompt components - DRY compliance."""

# JSON format instructions used across multiple steps
JSON_FORMAT_CORE = (
    """Output valid JSON only. Start with { and end with }. No markdown, yaml, or explanations."""
)

JSON_EXAMPLES_BLOCK = """
INVALID:
```json
{"field": "value"}
```

VALID:
{"field": "value"}"""

# Tool execution decision logic
TOOL_RESPONSE_LOGIC = """DECISION LOGIC:

MORE WORK NEEDED:
- tool_calls: [...] (tools to use)  
- response: "" (empty)

TASK FINISHED:
- tool_calls: [] (empty array)
- response: "complete answer" (REQUIRED - cannot be empty)

CRITICAL RULES:
- If tool_calls=[], response field MUST contain the final answer
- NEVER generate tool_calls=[] with response="" - this causes loops
- After multiple tool executions, summarize your accomplishments to complete the task"""


# Common response format template
def build_json_schema(fields: dict) -> str:
    """Build JSON schema from field definitions."""
    lines = ["{"]
    for field, description in fields.items():
        lines.append(f'  "{field}": "{description}",')
    if lines[-1].endswith(","):
        lines[-1] = lines[-1][:-1]  # Remove trailing comma
    lines.append("}")
    return "\n".join(lines)
