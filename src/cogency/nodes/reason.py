"""Reason node - pure reasoning and decision making."""
import time
from typing import List, Optional, Dict, Any

from cogency.llm import BaseLLM
from cogency.tools.base import BaseTool
from cogency.common.types import AgentState, ReasoningDecision
from cogency.utils.tracing import trace_node
from cogency.reasoning.parsing import ReactResponseParser
from cogency.reasoning.adaptive import StoppingReason
from cogency.streaming.messaging import AgentMessenger


INITIAL_REASON_PROMPT = """You are in a ReAct reasoning loop. Analyze the current situation and decide your next action.

CONTEXT: Look at the conversation history and any tool results from previous actions.
GOAL: {user_input}

Available tools: {tool_names}

Based on what you know so far, decide:
1. Do you have enough information to provide a complete answer? 
2. Or do you need to gather more information using tools?

First, explain your reasoning in a clear, concise way (1-2 sentences). Then provide your decision in JSON format.

REASONING: [Your step-by-step thinking about what you need to do]

JSON_DECISION:
- If you can answer completely: {{"action": "respond", "answer": "your complete answer"}}
- If you need one tool: {{"action": "use_tool", "tool_call": {{"name": "tool_name", "args": {{"param": "value"}}}}}}
- If you need multiple tools: {{"action": "use_tools", "tool_call": {{"calls": [{{"name": "tool1", "args": {{"param": "value"}}}}, {{"name": "tool2", "args": {{"param": "value"}}}}]}}}}"""

REFLECTION_PROMPT = """You are in a ReAct reasoning loop. You just received tool results - reflect on them and decide your next action.

GOAL: {user_input}
Available tools: {tool_names}

REFLECTION QUESTIONS:
1. Did the tool results help answer the user's question?
2. Are the results what you expected? Any errors or issues?
3. Do you need more information or can you provide a complete answer now?
4. If you need more info, what specific tools should you use next?

First, explain your reflection on the tool results (1-2 sentences). Then provide your decision in JSON format.

REASONING: [Your reflection on the tool results and next steps]

JSON_DECISION:
- If you can answer completely: {{"action": "respond", "answer": "your complete answer"}}
- If you need one tool: {{"action": "use_tool", "tool_call": {{"name": "tool_name", "args": {{"param": "value"}}}}}}
- If you need multiple tools: {{"action": "use_tools", "tool_call": {{"calls": [{{"name": "tool1", "args": {{"param": "value"}}}}, {{"name": "tool2", "args": {{"param": "value"}}}}]}}}}"""


@trace_node("reason")
async def reason_node(state: AgentState, *, llm: BaseLLM, tools: List[BaseTool], system_prompt: Optional[str] = None, config: Optional[Dict] = None) -> AgentState:
    """Reason: analyze context and decide next action (includes implicit reflection)."""
    context = state["context"]
    selected_tools = state.get("selected_tools", tools or [])
    controller = state.get("adaptive_controller")
    
    # Get streaming callback if available
    streaming_callback = None
    if config and "configurable" in config:
        streaming_callback = config["configurable"].get("streaming_callback")
    
    # Check adaptive reasoning limits if controller exists
    if controller:
        should_continue, stopping_reason = controller.should_continue_reasoning()
        if not should_continue:
            # Generate fallback response when reasoning should stop
            return await _generate_fallback_response(state, llm, stopping_reason, system_prompt)
    
    tool_info = ", ".join([f"{t.name}: {t.get_schema()}" for t in selected_tools]) if selected_tools else "no tools"
    
    messages = list(context.messages)
    messages.append({"role": "user", "content": context.current_input})
    
    # Determine if this is initial reasoning or reflection on tool results
    has_tool_results = state.get("execution_results") is not None
    
    # Choose appropriate prompt based on context
    if has_tool_results:
        # This is reflection after tool execution
        reasoning_prompt = REFLECTION_PROMPT.format(
            tool_names=tool_info,
            user_input=context.current_input
        )
    else:
        # This is initial reasoning
        reasoning_prompt = INITIAL_REASON_PROMPT.format(
            tool_names=tool_info,
            user_input=context.current_input
        )
    
    if system_prompt:
        reasoning_prompt = f"{system_prompt}\n\n{reasoning_prompt}"
    
    messages.insert(0, {"role": "system", "content": reasoning_prompt})
    
    llm_response = await llm.invoke(messages)
    context.add_message("assistant", llm_response)
    
    parser = ReactResponseParser()
    can_answer = parser.can_answer_directly(llm_response)
    
    # Extract intelligent reasoning text and stream it
    reasoning_text = parser.extract_reasoning(llm_response)
    if streaming_callback:
        await AgentMessenger.reason(streaming_callback, reasoning_text)
    
    # Store reasoning results in state
    state["reasoning_response"] = llm_response
    state["can_answer_directly"] = can_answer
    state["tool_calls"] = parser.extract_tool_calls(llm_response)
    state["direct_response"] = parser.extract_answer(llm_response) if can_answer else None
    
    # Determine next node
    if can_answer:
        state["next_node"] = "respond"
    elif state["tool_calls"]:
        state["next_node"] = "act"
    else:
        state["next_node"] = "respond"  # Fallback to respond if no clear action
    
    return state


async def _generate_fallback_response(state: AgentState, llm: BaseLLM, stopping_reason: StoppingReason, system_prompt: Optional[str] = None) -> AgentState:
    """Generate fallback response when reasoning loop should stop."""
    context = state["context"]
    
    # Generate a proper summary based on tool results in context
    summary_prompt = f"""Based on all the tool results and analysis in the conversation, provide a comprehensive answer to the user's original question. 

    Stopping reason: {stopping_reason}
    
    Synthesize all the information gathered from tool executions into a clear, helpful response that directly addresses what the user asked for."""
    
    final_messages = list(context.messages)
    final_messages.append({"role": "user", "content": summary_prompt})
    
    if system_prompt:
        summary_prompt = f"{system_prompt}\n\n{summary_prompt}"
    
    final_messages.insert(0, {"role": "system", "content": "Provide a clear, comprehensive summary based on all the tool results and reasoning shown in the conversation."})
    
    final_response = await llm.invoke(final_messages)
    context.add_message("assistant", final_response)
    
    # Set state for respond node
    state["context"] = context
    state["reasoning_decision"] = ReasoningDecision(
        should_respond=True, 
        response_text=final_response, 
        task_complete=True
    )
    state["last_node_output"] = final_response
    state["direct_response"] = final_response
    state["next_node"] = "respond"
    
    return state