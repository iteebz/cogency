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

Response format (JSON only):
- If you can answer completely: {{"action": "respond", "answer": "your complete answer"}}
- If you need one tool: {{"action": "use_tool", "tool_call": {{"name": "tool_name", "args": {{"param": "value"}}}}}}
- If you need multiple tools: {{"action": "use_tools", "tool_call": {{"calls": [{{"name": "tool1", "args": {{"param": "value"}}}}, {{"name": "tool2", "args": {{"param": "value"}}}}]}}}}

Think step by step about what information you have and what you still need. Output only valid JSON."""

RESPONSE_PROMPT = """Generate final response based on context and tool results.
Be conversational and helpful. Incorporate all relevant information."""


def _can_answer_directly(response: str) -> bool:
    """Check if LLM response indicates it can answer directly."""
    try:
        import json
        import re
        
        # Handle markdown code blocks
        response_cleaned = response.strip()
        if response_cleaned.startswith("```json"):
            json_match = re.search(r'```json\s*\n?(.*?)\n?```', response_cleaned, re.DOTALL)
            if json_match:
                response_cleaned = json_match.group(1).strip()
        elif response_cleaned.startswith("```"):
            json_match = re.search(r'```\s*\n?(.*?)\n?```', response_cleaned, re.DOTALL)
            if json_match:
                response_cleaned = json_match.group(1).strip()
        
        data = json.loads(response_cleaned)
        return data.get("action") == "respond"
    except (json.JSONDecodeError, KeyError):
        return False

def _extract_direct_response(response: str) -> str:
    """Extract direct answer from LLM response."""
    try:
        import json
        import re
        
        # Handle markdown code blocks
        response_cleaned = response.strip()
        if response_cleaned.startswith("```json"):
            json_match = re.search(r'```json\s*\n?(.*?)\n?```', response_cleaned, re.DOTALL)
            if json_match:
                response_cleaned = json_match.group(1).strip()
        elif response_cleaned.startswith("```"):
            json_match = re.search(r'```\s*\n?(.*?)\n?```', response_cleaned, re.DOTALL)
            if json_match:
                response_cleaned = json_match.group(1).strip()
        
        data = json.loads(response_cleaned)
        return data.get("answer", "")
    except (json.JSONDecodeError, KeyError):
        return ""

def _extract_tool_calls(response: str) -> Optional[str]:
    """Extract tool calls from LLM response for parsing."""
    try:
        import json
        import re
        
        # Handle markdown code blocks
        response_cleaned = response.strip()
        if response_cleaned.startswith("```json"):
            # Extract JSON from markdown code block
            json_match = re.search(r'```json\s*\n?(.*?)\n?```', response_cleaned, re.DOTALL)
            if json_match:
                response_cleaned = json_match.group(1).strip()
        elif response_cleaned.startswith("```"):
            # Extract from generic code block
            json_match = re.search(r'```\s*\n?(.*?)\n?```', response_cleaned, re.DOTALL)
            if json_match:
                response_cleaned = json_match.group(1).strip()
        
        data = json.loads(response_cleaned)
        if data.get("action") in ["use_tool", "use_tools"]:
            # Return the cleaned JSON for parsing by parse_tool_call
            return response_cleaned
    except (json.JSONDecodeError, KeyError):
        pass
    return None

def _complexity_score(user_input: str, tool_count: int) -> float:
    """Estimate query complexity for adaptive reasoning depth."""
    base = min(0.3, len(user_input) / 300)
    keywords = sum(1 for kw in ['analyze', 'compare', 'evaluate', 'research'] if kw in user_input.lower())
    tools = min(0.2, tool_count / 15)
    return max(0.1, min(1.0, base + keywords * 0.15 + tools))


@trace_node("react_loop")
async def react_loop_node(state: AgentState, llm: BaseLLM, tools: Optional[List[BaseTool]] = None, 
                         response_shaper: Optional[Dict[str, Any]] = None, config: Optional[Dict] = None) -> AgentState:
    """ReAct Loop Node: Full multi-step reason → act → observe cycle until task complete."""
    context = state["context"]
    selected_tools = state.get("selected_tools", tools or [])
    
    # Get streaming callback from config
    streaming_callback = None
    if config and "configurable" in config:
        streaming_callback = config["configurable"].get("streaming_callback")
    
    # Initialize adaptive control with complexity-based criteria
    complexity = _complexity_score(context.current_input, len(selected_tools))
    criteria = StoppingCriteria()
    criteria.max_iterations = max(3, int(complexity * 10))  # 3-10 iterations based on complexity
    
    controller = AdaptiveReasoningController(criteria)
    controller.start_reasoning()
    
    # Run multi-step ReAct loop with streaming support
    final_response = await react_loop_with_streaming(state, llm, selected_tools, controller, streaming_callback, response_shaper)
    
    return {
        "context": final_response["context"],
        "reasoning_decision": final_response["decision"],
        "last_node_output": final_response["text"]
    }


async def react_loop_with_streaming(state: AgentState, llm: BaseLLM, tools: List[BaseTool], 
                                   controller: AdaptiveReasoningController, 
                                   streaming_callback=None, response_shaper=None) -> Dict[str, Any]:
    """Streaming version of ReAct loop with polished real-time updates."""
    iteration = 0
    
    while True:
        should_continue, stopping_reason = controller.should_continue_reasoning()
        if not should_continue:
            if streaming_callback:
                await streaming_callback(f"\n💬 RESPOND: Sufficient information gathered, preparing final response...\n")
            return await _fallback_response(state, llm, stopping_reason, response_shaper)
            
        iteration += 1
        
        # Clean visual separation between cycles
        if iteration > 1 and streaming_callback:
            await streaming_callback(f"\n")
        
        # Stream reasoning phase
        if streaming_callback:
            await streaming_callback(f"🧠 REASON: Analyzing available information and deciding next action...\n")
        
        # REASON: What should I do next?
        reasoning = await reason_phase(state, llm, tools)
        
        # If agent decides it can answer directly (after considering all context)
        if reasoning["can_answer_directly"]:
            if streaming_callback:
                await streaming_callback(f"💬 RESPOND: Have sufficient information to provide complete answer\n")
            
            # Apply response shaping if configured
            final_text = reasoning["direct_response"]
            if response_shaper:
                from cogency.response_shaper import ResponseShaper
                shaper = ResponseShaper(llm)
                final_text = await shaper.shape(final_text, response_shaper)
            
            return {
                "context": state["context"],
                "text": final_text,
                "decision": ReasoningDecision(should_respond=True, response_text=final_text, task_complete=True)
            }
        
        # Check if we have tool calls to execute
        if not reasoning["tool_calls"]:
            if streaming_callback:
                await streaming_callback(f"💬 RESPOND: No additional tools needed, responding with current knowledge\n")
            
            # Apply response shaping if configured
            final_text = reasoning["response"]
            if response_shaper:
                from cogency.response_shaper import ResponseShaper
                shaper = ResponseShaper(llm)
                final_text = await shaper.shape(final_text, response_shaper)
            
            return {
                "context": state["context"], 
                "text": final_text,
                "decision": ReasoningDecision(should_respond=True, response_text=final_text, task_complete=True)
            }
        
        # Extract tool names for better streaming messages
        tool_call_str = reasoning["tool_calls"]
        tool_call = parse_tool_call(tool_call_str)
        
        # Stream action phase with specific tool names
        if streaming_callback:
            if isinstance(tool_call, MultiToolCall):
                tool_names = [call.name for call in tool_call.calls]
                if len(tool_names) == 1:
                    await streaming_callback(f"⚡ ACT: Calling {tool_names[0]} tool to gather needed information...\n")
                else:
                    tools_str = ", ".join(tool_names)
                    await streaming_callback(f"⚡ ACT: Calling {tools_str} tools to gather needed information...\n")
            elif isinstance(tool_call, ToolCall):
                await streaming_callback(f"⚡ ACT: Calling {tool_call.name} tool to gather needed information...\n")
            else:
                await streaming_callback(f"⚡ ACT: Executing tools to gather needed information...\n")
        
        # ACT: Execute the planned action
        action = await act_phase(reasoning, state, tools)
        
        # Stream observation phase with detailed messages
        if streaming_callback:
            if action.get("results", {}).get("success"):
                results = action.get("results", {}).get("results", [])
                if isinstance(tool_call, MultiToolCall):
                    tool_names = [call.name for call in tool_call.calls]
                    tools_str = ", ".join(tool_names)
                    await streaming_callback(f"👀 OBSERVE: Successfully gathered data from {tools_str} tools\n")
                elif isinstance(tool_call, ToolCall):
                    await streaming_callback(f"👀 OBSERVE: Successfully gathered data from {tool_call.name} tool\n")
                else:
                    await streaming_callback(f"👀 OBSERVE: Successfully gathered data from tools\n")
            else:
                await streaming_callback(f"❌ OBSERVE: Tool execution failed, will retry or use available information\n")
        
        # Update controller metrics
        controller.update_iteration_metrics(action.get("results", {}), action.get("time", 0))
    
    # Should never reach here due to controller limits
    return await _fallback_response(state, llm, "max_iterations", response_shaper)


async def react_loop(state: AgentState, llm: BaseLLM, tools: List[BaseTool], 
                    controller: AdaptiveReasoningController) -> Dict[str, Any]:
    """True multi-step ReAct: reason → act → observe → reason → act until agent decides it's done."""
    
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
        
        # Check if we have tool calls to execute
        if not reasoning["tool_calls"]:
            return {
                "context": state["context"], 
                "text": reasoning["response"],
                "decision": ReasoningDecision(should_respond=True, response_text=reasoning["response"], task_complete=True)
            }
        
        # ACT: Execute the planned action
        action = await act_phase(reasoning, state, tools)
        
        # OBSERVE: Results are now in context, continue reasoning about them
        # The magic happens in the next iteration where reason_phase sees the tool results
        # and decides: "Based on these results, should I use another tool or respond?"
        
        # Update controller metrics
        controller.update_iteration_metrics(action.get("results", {}), action.get("time", 0))
    
    # Should never reach here due to controller limits
    return await _fallback_response(state, llm, "max_iterations", response_shaper)


async def reason_phase(state: AgentState, llm: BaseLLM, tools: List[BaseTool]) -> Dict[str, Any]:
    """ReAct Reason: Think about what to do next."""
    context = state["context"]
    
    tool_info = ", ".join([f"{t.name}: {t.get_schema()}" for t in tools]) if tools else "no tools"
    
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
    
    # Skip validation for now since it's designed for old format
    # validated_response = validate_tools(tool_call_str, tools)
    # if validated_response != tool_call_str:
    #     tool_call_str = validated_response
    
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


async def _fallback_response(state: AgentState, llm: BaseLLM, stopping_reason, response_shaper=None) -> Dict[str, Any]:
    """Generate fallback response when reasoning loop ends."""
    context = state["context"]
    
    # Generate a proper summary based on tool results in context
    summary_prompt = f"""Based on all the tool results and analysis in the conversation, provide a comprehensive answer to the user's original question. 

    Stopping reason: {stopping_reason}
    
    Synthesize all the information gathered from tool executions into a clear, helpful response that directly addresses what the user asked for."""
    
    final_messages = list(context.messages)
    final_messages.append({"role": "user", "content": summary_prompt})
    final_messages.insert(0, {"role": "system", "content": "Provide a clear, comprehensive summary based on all the tool results and reasoning shown in the conversation."})
    
    final_response = await llm.invoke(final_messages)
    context.add_message("assistant", final_response)
    
    # Apply response shaping if configured
    final_text = final_response
    if response_shaper:
        from cogency.response_shaper import ResponseShaper
        shaper = ResponseShaper(llm)
        final_text = await shaper.shape(final_text, response_shaper)
    
    return {
        "context": context,
        "text": final_text,
        "decision": ReasoningDecision(should_respond=True, response_text=final_text, task_complete=True)
    }