"""Response prompt templates - clean and scannable."""

from typing import Dict, Optional

# Response prompt templates
FAILURE_PROMPT = """{identity}
A tool operation failed while trying to fulfill the user's request. Your goal is to generate a helpful response acknowledging the failure and suggesting next steps.

USER QUERY: "{query}"

FAILED TOOL DETAILS:
{failed_tools}

RESPONSE STRATEGY:
- Acknowledge what you attempted: "I tried to [specific action] but..."
- Explain the specific failure: permission denied, timeout, invalid input, etc.
- Suggest concrete alternatives: different tool, modified approach, manual steps
- Ask clarifying questions if the request was ambiguous
- Offer to retry with corrected parameters if error suggests a fix"""

JSON_PROMPT = """{identity}
Your goal is to generate a final response formatted as a JSON object.

JSON RESPONSE FORMAT (required):
{output_schema}

USER QUERY: "{query}"{tool_section}

RESPONSE STRATEGY:
- Populate JSON fields exactly as specified by the schema
- Incorporate relevant information from USER QUERY and TOOL RESULTS into JSON content
- Ensure JSON is valid, complete, and properly formatted
- Use tool results as evidence, synthesize don't just dump data"""

TOOL_RESULTS_PROMPT = """{identity}
Your goal is to generate a final, comprehensive response synthesizing the available information.

USER QUERY: "{query}"

TOOL RESULTS:
{tool_results}

RESPONSE STRATEGY:
- Lead with direct answer to the user's original question
- Use tool results as primary evidence, your knowledge as supplementary
- Synthesize multiple tool results into coherent narrative
- Address the user's intent, not just literal query
- Reference conversation context when building on previous exchanges
- Maintain conversational flow while being thorough"""

KNOWLEDGE_PROMPT = """{identity}
Your goal is to answer the user's question directly using your internal knowledge.

USER QUERY: "{query}"

RESPONSE STRATEGY:
- Answer the question directly from your training knowledge
- Provide context and explanation appropriate to the question complexity
- Acknowledge limitations of your knowledge cutoff when relevant
- Maintain conversational and helpful tone
- Be concise but comprehensive"""


def prompt_response(
    query: str,
    has_tool_results: bool = False,
    tool_summary: Optional[str] = None,
    identity: Optional[str] = None,
    output_schema: Optional[str] = None,
    failures: Optional[Dict[str, str]] = None,
) -> str:
    """Clean routing to response templates."""

    if identity:
        secure_identity = f"You are {identity}."
    else:
        secure_identity = "You are a helpful AI assistant."

    # Route to appropriate template
    if failures:
        failed_tools = "\n".join(
            [f"- Tool: {tool_name}\n- Reason: {error}" for tool_name, error in failures.items()]
        )
        prompt = FAILURE_PROMPT.format(
            identity=secure_identity, query=query, failed_tools=failed_tools
        )
    elif output_schema:
        tool_section = (
            f"\n\nTOOL RESULTS:\n{tool_summary}" if has_tool_results and tool_summary else ""
        )
        prompt = JSON_PROMPT.format(
            identity=secure_identity,
            output_schema=output_schema,
            query=query,
            tool_section=tool_section,
        )
    elif has_tool_results:
        prompt = TOOL_RESULTS_PROMPT.format(
            identity=secure_identity, query=query, tool_results=tool_summary
        )
    else:
        prompt = KNOWLEDGE_PROMPT.format(identity=secure_identity, query=query)

    # Add anti-JSON instruction when no JSON schema is expected
    if not output_schema:
        prompt += "\n\nCRITICAL: Respond in natural language only. Do NOT output JSON, reasoning objects, or tool_calls. This is your final response to the user."

    return prompt
