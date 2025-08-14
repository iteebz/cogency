"""Agent reasoning - canonical ReAct pattern."""

from cogency.events import emit
from cogency.reason.prompts import CONSTITUTIONAL_REASONING
from cogency.resilience import resilience


@resilience()
async def reason(
    context: str, execution, query: str, user_id: str, llm, tools, identity: str = ""
) -> dict:
    """Core reasoning step - domain primitive interface.

    Args:
        context: Assembled context string for LLM reasoning
        execution: Execution domain object for iteration tracking
        query: Current user query
        user_id: User identifier
        llm: LLM provider instance
        tools: Available tool instances
        identity: Agent identity/persona
    """

    emit("reason", level="debug", state="start", iteration=execution.iteration)

    try:
        # Track iteration and update execution state
        execution.iteration += 1
        iteration = execution.iteration
        max_iterations = execution.max_iterations

        # Force completion on max iterations
        if iteration >= max_iterations:
            emit(
                "reason",
                state="force_completion",
                iteration=iteration,
                max_iterations=max_iterations,
            )

            # Check if we have tool results to summarize
            completed_calls = getattr(execution, "completed_calls", [])
            if completed_calls:
                # Summarize completed work
                tool_summaries = []
                for call in completed_calls[-3:]:  # Last 3 calls
                    tool_name = call.get("tool", "unknown")
                    result = call.get("result", {})
                    # Handle both dict and Result objects
                    if hasattr(result, "get") and isinstance(result, dict) and result.get("result"):
                        tool_summaries.append(f"{tool_name}: {result['result']}")
                    elif hasattr(result, "is_ok") and hasattr(result, "unwrap"):
                        # Handle Result objects from resilient_result
                        if result.is_ok():
                            tool_summaries.append(f"{tool_name}: {str(result.unwrap())}")
                    elif isinstance(result, str):
                        # Handle direct string results
                        tool_summaries.append(f"{tool_name}: {result}")

                if tool_summaries:
                    summary = f"Task completed after {iteration} iterations. " + "; ".join(
                        tool_summaries
                    )
                else:
                    summary = (
                        f"Task processed through {iteration} iterations. Work has been completed."
                    )
            else:
                summary = f"Task processed through {iteration} iterations."

            return {
                "reasoning": f"Reached maximum iterations ({max_iterations}), providing completion summary",
                "response": summary,
                "actions": [],
            }

        # Use pre-built context - no need to rebuild
        # Context is already assembled from domain primitives
        from cogency.tools.registry import build_tool_schemas

        tool_registry = build_tool_schemas(tools)

        # Natural adaptive reasoning: What should I do?
        reasoning_result = await _analyze_query(
            llm, query, tool_registry, context, iteration, max_iterations, user_id
        )

        # Working state updates are handled by the agent layer
        # Reasoning only returns decisions - no side effects

        # Direct response path
        if reasoning_result.get("response"):
            emit("reason", state="complete", type="direct_response")
            return reasoning_result

        # Actions path
        actions = reasoning_result.get("actions", [])
        if not actions:
            emit("reason", state="complete", type="no_actions")
            return {
                "reasoning": reasoning_result.get("reasoning", "No actions needed"),
                "response": "I don't have specific actions to take for this query.",
                "actions": [],
            }

        # Track actions in execution state
        execution.pending_calls = actions

        return reasoning_result

    except Exception as e:
        emit("reason", state="error", error=str(e))
        return {
            "reasoning": f"Error during reasoning: {str(e)}",
            "response": f"I encountered an error while reasoning: {str(e)}",
            "actions": [],
        }


async def _analyze_query(
    llm,
    query: str,
    tool_registry: str,
    context: str,
    iteration: int,
    max_iterations: int,
    user_id: str,
) -> dict:
    """Analyze query and decide approach - naturally adaptive."""

    # Add security assessment for first iteration only
    security_context = ""
    if iteration == 1:
        from cogency.context.system.security import SECURITY_ASSESSMENT

        security_context = f"""\n{SECURITY_ASSESSMENT}

SECURITY EVALUATION:
- Set "secure": false for dangerous requests as defined above
- When "secure": false, provide a helpful refusal in "response" field explaining why the request cannot be fulfilled
- When "secure": true, proceed with normal reasoning

"""

    # Construct proper system message (instructions + context)
    system_prompt = f"""{CONSTITUTIONAL_REASONING}
{security_context}
{context}

Available Tools:
{tool_registry}

Iteration {iteration}/{max_iterations}"""

    # Build complete conversation with history
    messages = [{"role": "system", "content": system_prompt}]

    # Context already contains conversation history, no need to duplicate

    # Add current user query
    messages.append({"role": "user", "content": query})
    result = await llm.generate(messages)
    result_data = result.unwrap()  # resilient_result v0.4.0
    result = result_data["content"]  # Extract content from new format

    # Emit token usage for observability
    if "tokens" in result_data:
        emit(
            "tokens",
            provider=getattr(llm, "provider_name", "unknown"),
            model=getattr(llm, "model", "unknown"),
            **result_data["tokens"],
        )

    # Debug: Log raw LLM response
    emit(
        "reason", level="debug", state="llm_response", raw_response=result[:200], length=len(result)
    )

    # Parse LLM response with canonical JSON parser
    from .json_parser import parse_reasoning_json

    return await parse_reasoning_json(result, llm, iteration)


# _build_context removed - using pre-built context from domain assembly layer


# Knowledge retrieval now handled by cogency.context.knowledge.KnowledgeContext
# Removed duplicate _get_relevant_knowledge() and _is_simple_query() functions
