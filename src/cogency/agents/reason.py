"""Agent reasoning - canonical ReAct pattern."""

import json

from resilient_result import unwrap

# Canonical ReAct reasoning prompt
ADAPTIVE_REASONING_SYSTEM = """Analyze this query and respond appropriately.

Think as deeply as the question requires - no more, no less.

You must respond with a JSON object containing:
{
  "reasoning": "Brief explanation of approach",
  "response": "Direct answer for simple queries, null if actions needed",
  "actions": [{"name": "tool_name", "args": {"param": "value"}}]
}

DIRECT RESPONSE - Use "response" field ONLY for:
- Simple math: "What is 5+5?" → "10"
- Basic facts: "What color is the sky?" → "Blue"
- Greetings: "Hello" → "Hello! How can I help?"
- Identity: "Who are you?" → "I'm an AI assistant"

ACTIONS - Use "actions" array for:
- File operations, code writing, running commands
- Tasks requiring tools: "create", "build", "run", "execute"
- Any request to perform actions or make changes

FLOW:
- If simple query → set "response", leave "actions" empty
- If complex task needs tools → set "actions", leave "response" null
- If task is complete (after tool execution) → set "response" with summary, leave "actions" empty
- Always include "reasoning" to explain your approach

COMPLETION CRITERIA (CRITICAL):
- After 1-2 successful tool calls, provide response immediately
- MANDATORY: If you have taken actions and made progress, you MUST complete with a summary
- At maximum iterations, you MUST provide a response with available information
- NEVER generate actions=[] with response="" - this causes infinite loops
- Don't re-analyze successful tool results - use them directly
- If tools worked, complete the task - don't second-guess
- Prefer completion over perfectionism

STOP OVERTHINKING:
- Progress > Perfection
- Gaps in information are OK - respond with available data
- Don't endlessly analyze - use what you have"""


async def reason(state, llm, tools, identity: str = "") -> dict:
    """Core reasoning step - canonical ReAct pattern."""
    from cogency.events import emit

    emit("reason", state="start", iteration=getattr(state.execution, "iteration", 0))

    try:
        # Track iteration and update execution state
        state.execution.iteration += 1
        iteration = state.execution.iteration
        max_iterations = getattr(state.execution, "max_iterations", 10)

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
                    if isinstance(result, dict) and result.get("result"):
                        tool_summaries.append(f"{tool_name}: {result['result']}")

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
            llm, query, tool_registry, context, iteration, max_iterations
        )

        # Update workspace with reasoning insights
        if reasoning_result.get("reasoning"):
            state.workspace.thoughts.append(
                {
                    "iteration": state.execution.iteration,
                    "reasoning": reasoning_result["reasoning"],
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

        emit("reason", state="complete", type="actions_planned", actions=len(actions))
        return reasoning_result

    except Exception as e:
        emit("reason", state="error", error=str(e))
        return {
            "reasoning": f"Error during reasoning: {str(e)}",
            "response": f"I encountered an error while reasoning: {str(e)}",
            "actions": [],
        }


async def _analyze_query(
    llm, query: str, tool_registry: str, context: str, iteration: int, max_iterations: int
) -> dict:
    """Analyze query and decide approach - naturally adaptive."""
    from cogency.events import emit

    prompt = f"""{ADAPTIVE_REASONING_SYSTEM}

{context}

Query: "{query}"

Available Tools:
{tool_registry}

Iteration {iteration}/{max_iterations}

Respond with JSON only:"""

    messages = [{"role": "user", "content": prompt}]
    result = await llm.generate(messages)
    result = unwrap(result)

    # Debug: Log raw LLM response
    emit("reason", state="llm_response", raw_response=result[:200], length=len(result))

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

        # Ensure required fields exist
        return {
            "reasoning": parsed.get("reasoning", "No reasoning provided"),
            "response": parsed.get("response"),
            "actions": parsed.get("actions", []),
        }

    except json.JSONDecodeError as e:
        emit("reason", state="json_error", error=str(e), raw_response=result[:200])
        return {
            "reasoning": f"Analysis parsing failed: {e}",
            "response": "I had trouble understanding what to do. Could you rephrase your request?",
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

        if search_result.failure or not search_result.data:
            return ""

        # Format knowledge for context injection
        knowledge_items = []
        for result in search_result.data[:2]:  # Top 2 results only
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
