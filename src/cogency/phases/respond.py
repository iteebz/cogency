"""Respond node - final response formatting and personality."""

from typing import Dict, List, Optional

from cogency.decorators import phase

# Removed LangGraph dependency
from cogency.phases.base import Phase
from cogency.services import LLM
from cogency.state import State
from cogency.tools import Tool


class Respond(Phase):
    def __init__(self, llm, tools, identity=None, output_schema=None):
        super().__init__(
            respond,
            llm=llm,
            tools=tools,
            identity=identity,
            output_schema=output_schema,
        )

    def next_phase(self, state: State) -> str:
        return "END"  # End token, no longer using LangGraph


# Response prompt templates - clean and scannable
FAILURE_PROMPT = """{identity}
A tool operation failed while trying to fulfill the user's request. Your goal is to generate a helpful response acknowledging the failure and suggesting next steps.

USER QUERY: "{query}"

FAILED TOOL DETAILS:
{failed_tools}

RESPONSE STRATEGY:
- Acknowledge the tool failure gracefully without technical jargon
- Briefly explain what went wrong: "I encountered an issue when trying to..."
- Suggest concrete alternative approaches or ask for clarification
- Maintain a helpful and solution-focused tone
- Offer to retry with different parameters if applicable"""

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
    identity_line = f"You are {identity}. " if identity else ""

    # Route to appropriate template
    if failures:
        failed_tools = "\n".join(
            [f"- Tool: {tool_name}\n- Reason: {error}" for tool_name, error in failures.items()]
        )
        prompt = FAILURE_PROMPT.format(
            identity=identity_line, query=query, failed_tools=failed_tools
        )
    elif output_schema:
        tool_section = (
            f"\n\nTOOL RESULTS:\n{tool_summary}" if has_tool_results and tool_summary else ""
        )
        prompt = JSON_PROMPT.format(
            identity=identity_line,
            output_schema=output_schema,
            query=query,
            tool_section=tool_section,
        )
    elif has_tool_results:
        prompt = TOOL_RESULTS_PROMPT.format(
            identity=identity_line, query=query, tool_results=tool_summary
        )
    else:
        prompt = KNOWLEDGE_PROMPT.format(identity=identity_line, query=query)

    # Add anti-JSON instruction when no JSON schema is expected
    if not output_schema:
        prompt += "\n\nCRITICAL: Respond in natural language only. Do NOT output JSON, reasoning objects, or tool_calls. This is your final response to the user."

    return prompt


def collect_failures(state: State) -> Optional[Dict[str, str]]:
    """Collect all failure scenarios into unified dict."""
    failures = {}

    # Check for stop reason (reasoning failures)
    if state.stop_reason:
        user_error_message = getattr(
            state, "user_error_message", "I encountered an issue but will try to help."
        )
        failures["reasoning"] = user_error_message
        return failures

    # Check for tool failures in latest results
    for result in state.latest_tool_results:
        if result.outcome in ["failure", "error", "timeout"]:
            failures[result.name] = result.result or "Tool execution failed"

    return failures if failures else None


def format_tool_results(state: State) -> Optional[str]:
    """Extract and format tool results for response context."""
    if not state.latest_tool_results:
        return None

    # Format successful tool results only
    successful_results = [
        result
        for result in state.latest_tool_results[:5]
        if result.outcome not in ["failure", "error", "timeout"]
    ]

    if not successful_results:
        return None

    return "\n".join(
        [
            f"• {result.name}: {str(result.result or 'no result')[:200]}..."
            for result in successful_results
        ]
    )


@phase.respond()
async def respond(
    state: State,
    notifier,
    llm: LLM,
    tools: List[Tool],
    identity: Optional[str] = None,
    output_schema: Optional[str] = None,
) -> None:
    """Respond: generate final formatted response with personality."""
    await notifier("respond", state="generating")

    # Collect all context upfront - no branching ceremony
    failures = collect_failures(state)
    tool_results = format_tool_results(state)

    # Single decision point for prompt routing
    prompt = prompt_response(
        state.query,
        failures=failures,
        has_tool_results=bool(tool_results),
        tool_summary=tool_results,
        identity=identity,
        output_schema=output_schema,
    )

    # Single LLM call with unified error handling
    if llm is None:
        response_text = "I'm here to help. How can I assist you?"
    else:
        messages = state.get_conversation()
        messages.insert(0, {"role": "system", "content": prompt})

        llm_result = await llm.run(messages)
        response_text = (
            llm_result.data.strip()
            if llm_result.success
            else "I'm here to help. How can I assist you?"
        )

    await notifier("respond", state="complete", content=response_text[:100])

    # Update state
    state.add_message("assistant", response_text)
    if not state.response:
        state.response = response_text
    return state
