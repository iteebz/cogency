"""Respond node - final response formatting and personality."""

import asyncio
from typing import Dict, List, Optional

# Removed LangGraph dependency
from resilient_result import Result

from cogency.phases.base import Phase
from cogency.resilience import robust
from cogency.services.llm import BaseLLM
from cogency.state import State
from cogency.tools.base import BaseTool
from cogency.types.response import Response


class Respond(Phase):
    def __init__(self, **kwargs):
        super().__init__(respond, **kwargs)

    def next_phase(self, state: State) -> str:
        return "END"  # End token, no longer using LangGraph


# Response prompt templates - clean and scannable
FAILURE_PROMPT = """{identity}A tool operation failed while trying to fulfill the user's request. Your goal is to generate a helpful response acknowledging the failure and suggesting next steps.

USER QUERY: "{query}"

FAILED TOOL DETAILS:
{failed_tools}

RESPONSE STRATEGY:
- Acknowledge the tool failure gracefully without technical jargon
- Briefly explain what went wrong: "I encountered an issue when trying to..."
- Suggest concrete alternative approaches or ask for clarification
- Maintain a helpful and solution-focused tone
- Offer to retry with different parameters if applicable"""

JSON_PROMPT = """{identity}Your goal is to generate a final response formatted as a JSON object.

JSON RESPONSE FORMAT (required):
{json_schema}

USER QUERY: "{query}"{tool_section}

RESPONSE STRATEGY:
- Populate JSON fields exactly as specified by the schema
- Incorporate relevant information from USER QUERY and TOOL RESULTS into JSON content
- Ensure JSON is valid, complete, and properly formatted
- Use tool results as evidence, synthesize don't just dump data"""

TOOL_RESULTS_PROMPT = """{identity}Your goal is to generate a final, comprehensive response synthesizing the available information.

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

KNOWLEDGE_PROMPT = """{identity}Your goal is to answer the user's question directly using your internal knowledge.

USER QUERY: "{query}"

RESPONSE STRATEGY:
- Answer the question directly from your training knowledge
- Provide context and explanation appropriate to the question complexity
- Acknowledge limitations of your knowledge cutoff when relevant
- Maintain conversational and helpful tone
- Be concise but comprehensive"""


def prompt_response(
    query: str,
    system_prompt: Optional[str] = None,
    has_tool_results: bool = False,
    tool_summary: Optional[str] = None,
    identity: Optional[str] = None,
    json_schema: Optional[str] = None,
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
    elif json_schema:
        tool_section = (
            f"\n\nTOOL RESULTS:\n{tool_summary}" if has_tool_results and tool_summary else ""
        )
        prompt = JSON_PROMPT.format(
            identity=identity_line,
            json_schema=json_schema,
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
    if not json_schema:
        prompt += "\n\nCRITICAL: Respond in natural language only. Do NOT output JSON, reasoning objects, or tool_calls. This is your final response to the user."

    return f"{system_prompt}\n\n{prompt}" if system_prompt else prompt


# @robust.respond()  # DISABLED FOR DEBUGGING
async def respond(
    state: State,
    *,
    llm: BaseLLM,
    tools: List[BaseTool],
    system_prompt: Optional[str] = None,
    identity: Optional[str] = None,
    json_schema: Optional[str] = None,
) -> State:
    """Respond: generate final formatted response with personality."""
    # Direct access to state properties - no context wrapper needed

    # Start responding state
    await state.notify("respond", {"state": "responding"})

    # Streaming handled by Output

    # ALWAYS generate response - handle tool results, direct reasoning, or knowledge-based
    messages = state.get_conversation()
    response = Response()

    # Check for stopping reason
    stop_reason = state.stop_reason

    if stop_reason:
        # Handle reasoning stopped scenario with user-friendly message
        user_error_message = getattr(state, 'user_error_message', "I encountered an issue but will try to help.")
        if state.trace:
            await state.notify(
                "trace", {"message": f"Fallback response due to: {stop_reason}", "phase": "respond"}
            )

        # Use unified prompt function for fallback with user-friendly context
        failures = {"reasoning": user_error_message}
        prompt = prompt_response(
            state.query,
            system_prompt=system_prompt,
            failures=failures,
            identity=identity,
            json_schema=json_schema,
        )
        messages.insert(0, {"role": "system", "content": prompt})

        # Let @safe.respond() handle all LLM errors and fallbacks
        llm_result = await llm.run(messages)
        response.text = (
            llm_result.data.strip()
            if llm_result.success
            else "I encountered an issue but will try to help."
        )
        await state.notify("respond", f"🤖: {response.text}")
        await asyncio.sleep(0)
    else:
        # Generate response based on context and any tool results
        latest_results = state.get_latest_results()

        if latest_results:
            # Format tool results using schema-compliant structure
            tool_summary = "\n".join(
                [
                    f"• {call['name']}: {str(call.get('result', 'no result'))[:200]}..."
                    for call in latest_results[:5]  # Limit to 5 results
                ]
            )

            prompt = prompt_response(
                state.query,
                system_prompt=system_prompt,
                has_tool_results=True,
                tool_summary=tool_summary,
                identity=identity,
                json_schema=json_schema,
            )

            messages.insert(0, {"role": "system", "content": prompt})

            # Let @safe.respond() handle all LLM errors and fallbacks
            llm_result = await llm.run(messages)
            response.text = (
                llm_result.data.strip()
                if llm_result.success
                else "I encountered an issue while generating a response."
            )
            await state.notify("respond", f"🤖: {response.text}")
        else:
            # Check for any failure outcomes in latest results
            failures = {}
            if latest_results:
                for call in latest_results:
                    if call.get("outcome") in ["failure", "error", "timeout"]:
                        failures[call["name"]] = call.get("result", "Tool execution failed")

            if failures:
                prompt = prompt_response(
                    state.query,
                    system_prompt=system_prompt,
                    failures=failures,
                    identity=identity,
                    json_schema=json_schema,
                )
                messages.insert(0, {"role": "system", "content": prompt})

                # Let @safe.respond() handle all LLM errors and fallbacks
                llm_result = await llm.run(messages)
                response.text = (
                    llm_result.data.strip()
                    if llm_result.success
                    else "I encountered an issue while processing the request."
                )
                await state.notify("respond", f"🤖: {response.text}")
            else:
                # No tool results - answer with knowledge or based on conversation
                prompt = prompt_response(
                    state.query,
                    system_prompt=system_prompt,
                    has_tool_results=False,
                    identity=identity,
                    json_schema=json_schema,
                )
                messages.insert(0, {"role": "system", "content": prompt})

                # Let @safe.respond() handle all LLM errors and fallbacks
                llm_result = await llm.run(messages)
                response.text = (
                    llm_result.data.strip()
                    if llm_result.success
                    else "I'm here to help. How can I assist you?"
                )
                await state.notify("respond", f"🤖: {response.text}")

    # Add response to state conversation
    response_text = response.text if hasattr(response, "text") else response
    state.add_message("assistant", response_text)

    # Update flow state with clean assignment
    state.response = response_text

    return state
