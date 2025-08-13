"""Agent reasoning - canonical ReAct pattern."""

import json

# resilient_result v0.4.0 - unwrap is now a Result method
from cogency.resilience import resilience

# Constitutional Reasoning - Uses workspace architecture for intelligent planning
CONSTITUTIONAL_REASONING = """You are an intelligent reasoning agent. Analyze the query and provide your reasoning as a JSON object.

Your response should be a JSON object with:
{
  "secure": true/false,
  "assessment": "What you understand about this query",
  "approach": "How you plan to handle this",
  "response": "Direct answer for simple queries, null if actions needed",
  "actions": [{"name": "tool_name", "args": {"param": "value"}}]
}

INTELLIGENCE PRINCIPLES:
- Handle ambiguity gracefully - make reasonable assumptions
- Connect tasks to available tools intelligently
- "Create calculator script" with Files tool available → obviously use Files
- "Research topic" with Search tool available → obviously use Search
- Don't fail on reasonable requests - be helpful and adaptive
- ADAPT TO TOOL CONFLICTS: If file exists, use unique names, overwrite, or different approach
- LEARN FROM FAILURES: When tools fail, analyze the error and adapt your approach

CONFLICT RESOLUTION:
- File exists? → Use unique filename (add timestamp/random suffix) or ask to overwrite
- Command fails? → Try alternative commands or approaches
- Tool unavailable? → Use different tools or provide direct response
- Permission denied? → Suggest alternative paths or ask for clarification

EXAMPLES:
Simple: "What is 5+5?" → {"assessment": "Simple math", "response": "10"}
Complex: "Create calculator script" → {"assessment": "User wants Python calculator", "approach": "Create a simple Python script with basic operations", "actions": [{"name": "files", "args": {"action": "create", "path": "calculator.py", "content": "# Python calculator code"}}]}
Conflict: If calculator.py exists → {"assessment": "File exists, need unique name", "approach": "Create with timestamp suffix", "actions": [{"name": "files", "args": {"action": "create", "path": "calculator_2025_01_13.py", "content": "# Python calculator code"}}]}

BE INTELLIGENT, NOT RIGID. ADAPT TO CONFLICTS GRACEFULLY."""


@resilience()
async def reason(state, llm, tools, identity: str = "") -> dict:
    """Core reasoning step - canonical ReAct pattern."""
    from cogency.events import emit

    emit("reason", level="debug", state="start", iteration=getattr(state.execution, "iteration", 0))

    try:
        # Track iteration and update execution state
        state.execution.iteration += 1
        iteration = state.execution.iteration
        max_iterations = state.execution.max_iterations

        # CRITICAL: Force completion on max iterations (restored from archive)
        if iteration >= max_iterations:
            emit(
                "reason",
                state="force_completion",
                iteration=iteration,
                max_iterations=max_iterations,
            )

            # Check if we have tool results to summarize
            completed_calls = getattr(state.execution, "completed_calls", [])
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

        # Build context for reasoning with automatic knowledge retrieval
        query = state.query
        user_id = state.user_id
        context = await _build_context(state, query, user_id)
        tool_registry = _build_tool_registry(tools)

        # Natural adaptive reasoning: What should I do?
        reasoning_result = await _analyze_query(
            llm, state, query, tool_registry, context, iteration, max_iterations
        )

        # Update workspace with constitutional reasoning insights
        if reasoning_result.get("assessment"):
            state.workspace.assessment = reasoning_result["assessment"]

        if reasoning_result.get("approach"):
            state.workspace.approach = reasoning_result["approach"]

        # Track all reasoning iterations
        state.workspace.thoughts.append(
            {
                "iteration": state.execution.iteration,
                "assessment": reasoning_result.get("assessment", ""),
                "approach": reasoning_result.get("approach", ""),
                "timestamp": state.last_updated,
            }
        )

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
        state.execution.pending_calls = actions

        return reasoning_result

    except Exception as e:
        emit("reason", state="error", error=str(e))
        return {
            "reasoning": f"Error during reasoning: {str(e)}",
            "response": f"I encountered an error while reasoning: {str(e)}",
            "actions": [],
        }


async def _analyze_query(
    llm, state, query: str, tool_registry: str, context: str, iteration: int, max_iterations: int
) -> dict:
    """Analyze query and decide approach - naturally adaptive."""
    from cogency.events import emit

    # Add security assessment for first iteration only
    security_context = ""
    if iteration == 1:
        from cogency.security import SECURITY_ASSESSMENT

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

    # Add conversation history (user/assistant alternation)
    conversation_history = state.messages()
    messages.extend(conversation_history)

    # Add current user query
    messages.append({"role": "user", "content": query})
    result = await llm.generate(messages)
    result = result.unwrap()  # resilient_result v0.4.0

    # Debug: Log raw LLM response
    emit(
        "reason", level="debug", state="llm_response", raw_response=result[:200], length=len(result)
    )

    try:
        # Try to extract JSON if LLM adds extra text
        response_text = result.strip()

        # Look for JSON object in response
        start_idx = response_text.find("{")
        end_idx = response_text.rfind("}")

        if start_idx >= 0 and end_idx > start_idx:
            json_text = response_text[start_idx : end_idx + 1]
            parsed = json.loads(json_text)
        else:
            # Fallback to full response
            parsed = json.loads(response_text)

        # Check security assessment for iteration 1
        if iteration == 1 and parsed.get("secure") is False:
            emit("reason", state="security_violation", iteration=iteration)
            return {
                "reasoning": parsed.get("reasoning", "Security assessment failed"),
                "response": parsed.get("response", "I cannot assist with that request."),
                "actions": [],
            }

        # Constitutional reasoning structure
        return {
            "assessment": parsed.get("assessment", "No assessment provided"),
            "approach": parsed.get("approach", "No approach specified"),
            "response": parsed.get("response"),
            "actions": parsed.get("actions", []),
        }

    except json.JSONDecodeError as e:
        emit("reason", state="json_error", error=str(e), raw_response=result[:200])

        # CONSTITUTIONAL FIX: Send response back to LLM for self-correction
        # Don't use heuristics - let the LLM fix its own formatting

        correction_prompt = f"""You provided this response but it wasn't valid JSON:
{result}

Please provide the same reasoning as a valid JSON object with this exact structure:
{{
  "secure": true,
  "assessment": "what you understand about this query",
  "approach": "how you plan to handle this",
  "response": "your response here or null if actions needed",
  "actions": [list of actions if any]
}}

RESPOND WITH ONLY THE JSON OBJECT:"""

        try:
            correction_messages = [
                {
                    "role": "system",
                    "content": "Convert the previous response to valid JSON format.",
                },
                {"role": "user", "content": correction_prompt},
            ]

            correction_result = await llm.generate(correction_messages)
            correction_result = correction_result.unwrap()

            # Try to parse the corrected response
            corrected_json = json.loads(correction_result.strip())

            emit(
                "reason",
                state="json_corrected",
                original_length=len(result),
                corrected_length=len(correction_result),
            )

            return {
                "assessment": corrected_json.get("assessment", "Self-corrected assessment"),
                "approach": corrected_json.get("approach", "Self-corrected approach"),
                "response": corrected_json.get("response"),
                "actions": corrected_json.get("actions", []),
            }

        except Exception as correction_error:
            # LLM couldn't self-correct - use original response as direct answer
            emit("reason", state="json_correction_failed", error=str(correction_error))

            return {
                "assessment": "JSON formatting failed, using natural language response",
                "approach": "Direct response",
                "response": result.strip(),
                "actions": [],
            }


async def _build_context(state, query: str, user_id: str) -> str:
    """Build context from state for reasoning with automatic knowledge retrieval."""
    base_context = state.context()

    # Automatically query relevant knowledge for complex queries
    knowledge_context = await _get_relevant_knowledge(query, user_id)

    if knowledge_context:
        return f"{base_context}\n\nRELEVANT KNOWLEDGE:\n{knowledge_context}"

    return base_context


async def _get_relevant_knowledge(query: str, user_id: str) -> str:
    """Automatically retrieve relevant knowledge for query context."""
    from cogency.events import emit

    # Skip retrieval for simple queries that don't need memory
    if _is_simple_query(query):
        return ""

    try:
        import aiosqlite

        from cogency.providers import detect_embed
        from cogency.semantic import semantic_search
        from cogency.storage import SQLite

        embedder = detect_embed()
        store = SQLite()
        await store._ensure_schema()

        async with aiosqlite.connect(store.db_path) as db:
            search_result = await semantic_search(
                embedder=embedder,
                query=query,
                db_connection=db,
                user_id=user_id,
                top_k=3,  # Limit to most relevant
                threshold=0.75,  # Higher threshold for automatic retrieval
            )

        if search_result.failure or not search_result.unwrap():
            return ""

        # Format knowledge for context injection
        knowledge_items = []
        for result in search_result.unwrap()[:2]:  # Top 2 results only
            topic = result["metadata"].get("topic", "Knowledge")
            content = result["content"][:200]  # Truncate for context efficiency
            knowledge_items.append(f"- {topic}: {content}...")

        emit("memory", operation="auto_retrieval", results=len(knowledge_items), query=query)
        return "\n".join(knowledge_items)

    except Exception as e:
        emit("memory", operation="auto_retrieval", status="error", error=str(e))
        return ""


def _is_simple_query(query: str) -> bool:
    """Determine if query is simple enough to skip knowledge retrieval."""
    query_lower = query.lower().strip()

    # Simple greetings and basic questions
    simple_patterns = [
        "hello",
        "hi",
        "hey",
        "thanks",
        "thank you",
        "what time",
        "what's the weather",
        "what day",
        "who are you",
        "what are you",
        "how are you",
    ]

    # Math or basic factual queries
    if (
        any(pattern in query_lower for pattern in ["what is", "calculate", "compute"])
        and len(query) < 50
    ):
        return True

    return any(pattern in query_lower for pattern in simple_patterns)


def _build_tool_registry(tools) -> str:
    """Build complete tool registry for LLM."""
    if not tools:
        return "No tools available."

    descriptions = []
    for tool in tools:
        descriptions.append(f"- {tool.name}: {tool.description}")
        descriptions.append(f"  Schema: {getattr(tool, 'schema', 'No schema')}")

        for example in getattr(tool, "examples", []):
            descriptions.append(f"  Example: {example}")

        for rule in getattr(tool, "rules", []):
            descriptions.append(f"  Rule: {rule}")

    return "\n".join(descriptions)
