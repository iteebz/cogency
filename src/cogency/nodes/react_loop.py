"""Pure cognition - decide → execute → respond."""
import time
from typing import Dict, Any, Optional, List
from cogency.llm import BaseLLM
from cogency.tools.base import BaseTool
from cogency.types import AgentState, ReasoningDecision
from cogency.utils import validate_tools
from cogency.utils.trace import trace_node
from cogency.utils.tool_execution import parse_tool_call, execute_single_tool, execute_parallel_tools
from cogency.utils.adaptive_reasoning import AdaptiveReasoningController, StoppingCriteria, StoppingReason
from cogency.schemas import ToolCall, MultiToolCall

REASON_PROMPT = """You are in a ReAct reasoning loop. Analyze the current situation and decide your next action.

CONTEXT: Look at the conversation history and any tool results from previous actions.
GOAL: {user_input}

Available tools: {tool_names}

Based on what you know so far, decide:
1. Do you have enough information to provide a complete answer? 
2. Or do you need to gather more information using tools?

Response format:
- If you can answer completely: DIRECT_RESPONSE: [your complete answer]
- If you need more info: TOOL_NEEDED: tool_name(args) or [tool1(args), tool2(args)]

Think step by step about what information you have and what you still need."""

RESPONSE_PROMPT = """Generate final response based on context and tool results.
Be conversational and helpful. Incorporate all relevant information."""


def _can_answer_directly(response: str) -> bool:
    return response.strip().startswith("DIRECT_RESPONSE:")

def _extract_direct_response(response: str) -> str:
    return response.replace("DIRECT_RESPONSE:", "").strip()

def _extract_tool_calls(response: str) -> Optional[str]:
    if "TOOL_NEEDED:" in response:
        return response.split("TOOL_NEEDED:", 1)[1].strip()
    return None

def _complexity_score(user_input: str, tool_count: int) -> float:
    """Estimate query complexity for adaptive reasoning depth."""
    base = min(0.3, len(user_input) / 300)
    keywords = sum(1 for kw in ['analyze', 'compare', 'evaluate', 'research'] if kw in user_input.lower())
    tools = min(0.2, tool_count / 15)
    return max(0.1, min(1.0, base + keywords * 0.15 + tools))


@trace_node("react_loop")
async def react_loop_node(state: AgentState, llm: BaseLLM, tools: Optional[List[BaseTool]] = None, 
                         prompt_fragments: Optional[Dict[str, str]] = None) -> AgentState:
    """ReAct Loop Node: Full multi-turn reason → act → observe cycle until task complete."""
    context = state["context"]
    selected_tools = state.get("selected_tools", tools or [])
    
    # Initialize adaptive control with complexity-based criteria
    complexity = _complexity_score(context.current_input, len(selected_tools))
    criteria = StoppingCriteria()
    criteria.max_iterations = max(3, int(complexity * 10))  # 3-10 iterations based on complexity
    
    controller = AdaptiveReasoningController(criteria)
    controller.start_reasoning()
    
    # Run multi-turn ReAct loop
    final_response = await react_loop(state, llm, selected_tools, controller)
    
    return {
        "context": final_response["context"],
        "reasoning_decision": final_response["decision"],
        "last_node_output": final_response["text"]
    }


async def react_loop(state: AgentState, llm: BaseLLM, tools: List[BaseTool], 
                    controller: AdaptiveReasoningController) -> Dict[str, Any]:
    """True multi-turn ReAct: reason → act → observe → reason → act until agent decides it's done."""
    
    while True:
        should_continue, stopping_reason = controller.should_continue_reasoning()
        if not should_continue:
            return await _fallback_response(state, llm, stopping_reason)
            
        # REASON: What should I do next?
        reasoning = await reason_phase(state, llm, tools)
        
        # If agent decides it can answer directly (after considering all context)
        if reasoning["can_answer_directly"]:
            return {
                "context": state["context"],
                "text": reasoning["direct_response"],
                "decision": ReasoningDecision(should_respond=True, response_text=reasoning["direct_response"], task_complete=True)
            }
        
        # ACT: Execute the planned action
        action = await act_phase(reasoning, state, tools)
        
        # OBSERVE: Results are now in context, continue reasoning about them
        # The magic happens in the next iteration where reason_phase sees the tool results
        # and decides: "Based on these results, should I use another tool or respond?"
        
        # Update controller metrics
        controller.update_iteration_metrics(action.get("results", {}), action.get("time", 0))
    
    # Should never reach here due to controller limits
    return await _fallback_response(state, llm, "max_iterations")


async def reason_phase(state: AgentState, llm: BaseLLM, tools: List[BaseTool]) -> Dict[str, Any]:
    """ReAct Reason: Think about what to do next."""
    context = state["context"]
    
    tool_info = ", ".join([f"{t.name} ({t.description})" for t in tools]) if tools else "no tools"
    
    messages = list(context.messages)
    messages.append({"role": "user", "content": context.current_input})
    messages.insert(0, {"role": "system", "content": REASON_PROMPT.format(
        tool_names=tool_info,
        user_input=context.current_input
    )})
    
    llm_response = await llm.invoke(messages)
    context.add_message("assistant", llm_response)
    
    return {
        "response": llm_response,
        "can_answer_directly": _can_answer_directly(llm_response),
        "tool_calls": _extract_tool_calls(llm_response),
        "direct_response": _extract_direct_response(llm_response) if _can_answer_directly(llm_response) else None
    }


async def act_phase(reasoning: Dict[str, Any], state: AgentState, tools: List[BaseTool]) -> Dict[str, Any]:
    """ReAct Act: Execute tools based on reasoning. Results go into context for next reasoning cycle."""
    start_time = time.time()
    
    # Get tool calls from reasoning
    tool_call_str = reasoning["tool_calls"]
    if not tool_call_str:
        return {"type": "no_action", "time": time.time() - start_time}
    
    context = state["context"]
    
    # Validate and parse tool calls
    if tools:
        validated_response = validate_tools(tool_call_str, tools)
        if validated_response != tool_call_str:
            tool_call_str = validated_response
    
    tool_call = parse_tool_call(tool_call_str)
    execution_results = {}
    
    # Execute tools and add results to context (this is the OBSERVE step)
    if isinstance(tool_call, MultiToolCall):
        tool_calls_for_execution = [(call.name, call.args) for call in tool_call.calls]
        execution_results = await execute_parallel_tools(tool_calls_for_execution, tools, context)
    elif isinstance(tool_call, ToolCall):
        tool_name, parsed_args, tool_output = await execute_single_tool(
            tool_call.name, tool_call.args, tools
        )
        
        if isinstance(tool_output, dict) and tool_output.get("success") is False:
            # Add error to context so agent can reason about it
            error_msg = f"Tool {tool_name} failed: {tool_output.get('error')}"
            context.add_message("system", error_msg)
            execution_results = {"success": False, "errors": [error_msg]}
        else:
            # Add successful result to context
            result = tool_output.get("result") if isinstance(tool_output, dict) else tool_output
            context.add_message("system", f"Tool {tool_name} result: {result}")
            context.add_tool_result(tool_name, parsed_args, result)
            execution_results = {"success": True, "results": [result]}
    
    return {
        "type": "tool_execution",
        "results": execution_results,
        "time": time.time() - start_time
    }


async def respond_phase(action: Dict[str, Any], state: AgentState, llm: BaseLLM) -> Dict[str, Any]:
    """Generate final response based on action results."""
    context = state["context"]
    final_messages = list(context.messages)
    
    # Context-aware prompt based on action success
    results = action.get("results", {})
    if results.get("success"):
        system_prompt = RESPONSE_PROMPT
    else:
        system_prompt = "Generate helpful response acknowledging tool failures and providing alternatives."
    
    final_messages.insert(0, {"role": "system", "content": system_prompt})
    
    final_response = await llm.invoke(final_messages)
    context.add_message("assistant", final_response)
    
    return {
        "context": context,
        "text": final_response,
        "decision": ReasoningDecision(should_respond=True, response_text=final_response, task_complete=True)
    }


async def _fallback_response(state: AgentState, llm: BaseLLM, stopping_reason) -> Dict[str, Any]:
    """Generate fallback response when reasoning loop ends."""
    context = state["context"]
    
    fallback_text = "I've completed my reasoning process. Here's my response based on the analysis."
    
    # Use last assistant message if available
    final_messages = list(context.messages)
    if final_messages:
        last_response = next((msg["content"] for msg in reversed(final_messages) if msg["role"] == "assistant"), fallback_text)
        return {
            "context": context,
            "text": last_response,
            "decision": ReasoningDecision(should_respond=True, response_text=last_response, task_complete=True)
        }
    
    return {
        "context": context,
        "text": fallback_text,
        "decision": ReasoningDecision(should_respond=True, response_text=fallback_text, task_complete=True)
    }