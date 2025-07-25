"""Respond node - final response formatting and personality."""

import asyncio
from typing import Dict, List, Optional

from cogency.services.llm import BaseLLM
from cogency.state import State
from cogency.tools.base import BaseTool
from cogency.types.response import Response
from cogency.utils.parsing import fallback_response
from cogency.utils.results import ActionResult

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
    original_query: str,
    system_prompt: Optional[str] = None,
    has_tool_results: bool = False,
    tool_results_summary: Optional[str] = None,
    identity: Optional[str] = None,
    json_schema: Optional[str] = None,
    failure_details: Optional[Dict[str, str]] = None,
) -> str:
    """Clean routing to response templates."""
    identity_line = f"You are {identity}. " if identity else ""

    # Route to appropriate template
    if failure_details:
        failed_tools = "\n".join(
            [
                f"- Tool: {tool_name}\n- Reason: {error}"
                for tool_name, error in failure_details.items()
            ]
        )
        prompt = FAILURE_PROMPT.format(
            identity=identity_line, query=original_query, failed_tools=failed_tools
        )
    elif json_schema:
        tool_section = (
            f"\n\nTOOL RESULTS:\n{tool_results_summary}"
            if has_tool_results and tool_results_summary
            else ""
        )
        prompt = JSON_PROMPT.format(
            identity=identity_line,
            json_schema=json_schema,
            query=original_query,
            tool_section=tool_section,
        )
    elif has_tool_results:
        prompt = TOOL_RESULTS_PROMPT.format(
            identity=identity_line, query=original_query, tool_results=tool_results_summary
        )
    else:
        prompt = KNOWLEDGE_PROMPT.format(identity=identity_line, query=original_query)

    # Add anti-JSON instruction when no JSON schema is expected
    if not json_schema:
        prompt += "\n\nCRITICAL: Respond in natural language only. Do NOT output JSON, reasoning objects, or tool_calls. This is your final response to the user."

    return f"{system_prompt}\n\n{prompt}" if system_prompt else prompt


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
    context = state["context"]

    # Start responding state
    await state.output.state("responding")

    # Streaming handled by Output

    # ALWAYS generate response - handle tool results, direct reasoning, or knowledge-based
    final_messages = list(context.messages)
    final_response = Response()

    # Check for stopping reason
    stopping_reason = state.stopping_reason

    if stopping_reason:
        # Handle reasoning stopped scenario with user-friendly message
        user_error_message = state.get(
            "user_error_message", "I encountered an issue but will try to help."
        )
        await state.output.trace(f"Fallback response due to: {stopping_reason}", node="respond")

        # Use unified prompt function for fallback with user-friendly context
        failure_details = {"reasoning": user_error_message}
        prompt = prompt_response(
            context.query,
            system_prompt=system_prompt,
            failure_details=failure_details,
            identity=identity,
            json_schema=json_schema,
        )
        final_messages.insert(0, {"role": "system", "content": prompt})

        # Generate the fallback response
        response_result = await llm.run(final_messages)
        if not response_result.success:
            final_response = fallback_response(Exception(response_result.error), json_schema)
            await state.output.update(f"🤖: {final_response}")
        else:
            final_response.text = response_result.data.strip()
            await state.output.update(f"🤖: {final_response.text}")
            await asyncio.sleep(0)
    else:
        # Generate response based on context and any tool results
        action_result = state.action_result
        direct_response = state.direct_response

        if direct_response:
            # Add debug trace for JSON leakage
            await state.output.trace(
                f"Using direct_response: {type(direct_response)} - {str(direct_response)[:100]}...",
                node="respond",
            )
            final_response.text = direct_response
            await state.output.update(f"🤖: {final_response.text}")
        elif action_result and action_result.success:
            # Format tool results for display - handle both dict and list formats
            results_data = action_result.data
            if isinstance(results_data, dict):
                results = results_data.get("results", [])
            else:
                results = results_data if isinstance(results_data, list) else []

            tool_results_summary = "\n".join(
                [
                    f"• {result.get('tool_name', 'unknown')}: {str(result.get('result', 'no result'))[:200]}..."
                    for result in results[:5]  # Limit to 5 results
                ]
            )

            response_prompt = prompt_response(
                context.query,
                system_prompt=system_prompt,
                has_tool_results=True,
                tool_results_summary=tool_results_summary,
                identity=identity,
                json_schema=json_schema,
            )

            final_messages.insert(0, {"role": "system", "content": response_prompt})

            # Generate the main response
            response_result = await llm.run(final_messages)
            if not response_result.success:
                final_response = fallback_response(Exception(response_result.error), json_schema)
                await state.output.update(f"🤖: {final_response}")
            else:
                final_response.text = response_result.data
                await state.output.update(f"🤖: {final_response.text}")
        elif action_result and not action_result.success:
            # Format failure details - handle both dict and list formats
            results_data = action_result.data
            if isinstance(results_data, dict):
                results = results_data.get("results", [])
            else:
                results = results_data if isinstance(results_data, list) else []

            failure_details = {}
            for result in results:
                tool_name = result.get("tool_name", "unknown")
                error = result.get("error", "Tool execution failed")
                failure_details[tool_name] = error

            response_prompt = prompt_response(
                context.query,
                system_prompt=system_prompt,
                failure_details=failure_details,
                identity=identity,
                json_schema=json_schema,
            )
            final_messages.insert(0, {"role": "system", "content": response_prompt})

            # Generate the main response
            response_result = await llm.run(final_messages)
            if not response_result.success:
                final_response = fallback_response(Exception(response_result.error), json_schema)
                await state.output.update(f"🤖: {final_response}")
            else:
                final_response.text = response_result.data
                await state.output.update(f"🤖: {final_response.text}")
        else:
            # No tool results - answer with knowledge or based on conversation
            response_prompt = prompt_response(
                context.query,
                system_prompt=system_prompt,
                has_tool_results=False,
                identity=identity,
                json_schema=json_schema,
            )
            final_messages.insert(0, {"role": "system", "content": response_prompt})

            # Generate the main response
            response_result = await llm.run(final_messages)
            if not response_result.success:
                fallback_text = fallback_response(Exception(response_result.error), json_schema)
                final_response.text = fallback_text
                await state.output.update(f"🤖: {fallback_text}")
            else:
                final_response.text = response_result.data
                await state.output.update(f"🤖: {final_response.text}")

    # Add response to context
    response_text = final_response.text if hasattr(final_response, "text") else final_response
    context.add_message("assistant", response_text)

    # Update flow state
    state["final_response"] = response_text

    # Store response data directly in state
    state["reasoning_decision"] = ActionResult.ok(
        data={
            "should_respond": True,
            "response_text": response_text,
            "task_complete": True,
        }
    )
    state["last_node_output"] = response_text
    state["next_node"] = "END"

    # Clear reasoning_response to prevent leakage
    state["reasoning_response"] = None

    return state
