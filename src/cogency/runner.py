"""Canonical agent execution - domain coordination primitive."""

from cogency.act import act
from cogency.context.assembly import build_context
from cogency.context.conversation import add_message
from cogency.context.task import start_task
from cogency.events import emit
from cogency.reason import reason


async def run_agent(
    query: str,
    user_id: str = "default",
    llm=None,
    tools=None,
    memory=None,
    max_iterations: int = 5,
    identity: str = "",
    conversation_id: str = None,
) -> tuple[str, str]:
    """Execute agent query - canonical domain coordination.

    Args:
        query: User query
        user_id: User identifier
        llm: LLM provider instance
        tools: Available tool instances
        memory: Memory instance (optional)
        max_iterations: Max reasoning iterations
        identity: Agent identity/persona
        conversation_id: Existing conversation (optional)

    Returns:
        (response, conversation_id) - for caller persistence
    """
    if not llm:
        from cogency.providers import detect_llm

        llm = detect_llm()

    if not tools:
        tools = []

    # Start task with domain primitives
    session, conversation, working_state, execution = await start_task(
        query, user_id, conversation_id, max_iterations=max_iterations
    )

    try:
        # Add user query to conversation
        add_message(conversation, "user", query)

        # Memory operations
        if memory:
            await memory.load(user_id)
            await memory.remember(user_id, query, human=True)

        # ReAct loop - canonical domain coordination
        for iteration in range(max_iterations):
            emit("agent", level="debug", state="iteration", iteration=iteration)
            execution.iteration = iteration + 1

            # Build context from domain primitives
            context = await build_context(
                conversation=conversation,
                working_state=working_state,
                execution=execution,
                tools=tools,
                memory=memory,
                user_id=user_id,
                query=query,
                iteration=execution.iteration,
            )

            # Reason with domain primitives
            reasoning = await reason(
                context=context,
                execution=execution,
                query=query,
                user_id=user_id,
                llm=llm,
                tools=tools,
                identity=identity,
            )

            reasoning_data = reasoning.unwrap()

            # Direct response path
            if reasoning_data.get("response"):
                response = reasoning_data["response"]
                add_message(conversation, "assistant", response)
                break

            # Actions path
            actions = reasoning_data.get("actions", [])
            if actions:
                # Store and execute actions
                from cogency.context.execution import finish_tools, set_tool_calls

                set_tool_calls(execution, actions)
                act_result = await act(actions, tools, execution)

                if act_result.success:
                    finish_tools(execution, act_result.unwrap().get("results", []))

                # Add tool result to conversation
                summary = (
                    act_result.unwrap().get("summary", "Tools executed")
                    if act_result.success
                    else f"Error: {act_result.error}"
                )
                add_message(conversation, "assistant", f"Tool execution: {summary}")
                continue

            # No actions and no response
            response = "Unable to determine next steps for this request."
            break
        else:
            # Max iterations reached
            response = f"Task processed through {max_iterations} iterations."

        # Learn from response
        if memory and response:
            await memory.remember(user_id, response, human=False)

            # Domain learning operations
            from cogency.context.knowledge import extract
            from cogency.context.memory import learn

            await learn(conversation, working_state, user_id, memory)

            # Extract knowledge from substantial conversations
            if _should_extract_knowledge(query, response):
                await extract(conversation, working_state, user_id, memory)

        emit("agent", state="complete", response_length=len(response))
        return response, conversation.conversation_id

    except Exception as e:
        emit("agent", state="error", error=str(e))
        return f"Error: {str(e)}", conversation.conversation_id


def _should_extract_knowledge(query: str, response: str) -> bool:
    """Determine if conversation warrants knowledge extraction."""
    # Skip short interactions
    if len(query) < 20 or len(response) < 50:
        return False

    # Skip simple greetings
    simple_patterns = ["hello", "hi", "hey", "thanks", "what time", "who are you"]
    query_lower = query.lower().strip()

    if any(pattern in query_lower for pattern in simple_patterns):
        return False

    # Extract from substantial conversations
    return len(query) >= 100 or len(response) >= 200
