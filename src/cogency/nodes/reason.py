"""Unified reasoning node - THINK+PLAN+REFLECT merged into pure cognition."""
from typing import Dict, Any, Optional, List
from cogency.llm import BaseLLM
from cogency.tools.base import BaseTool
from cogency.types import AgentState, ReasoningDecision
from cogency.utils import validate_tools
from cogency.utils.trace import trace_node
from cogency.utils.tool_execution import parse_tool_call, execute_single_tool, execute_parallel_tools
from cogency.schemas import ToolCall, MultiToolCall

REASON_PROMPT = """You are an AI assistant analyzing a user request to determine the best response strategy.

Available tools: {tool_names}

USER REQUEST: {user_input}

ANALYSIS:
1. Can you answer this request directly with your existing knowledge?
2. Do you need to use tools to gather information or perform actions?
3. Which specific tools would be most helpful?

DECISION RULES:
- If you have sufficient knowledge to provide a complete, helpful answer → respond directly
- If you need current information, calculations, or actions → use tools
- Be decisive: avoid tools for simple questions you can answer well

RESPONSE FORMAT:
If responding directly:
DIRECT_RESPONSE: [your complete response here]

If tools needed:
TOOL_NEEDED: tool_name(arg1="value1", arg2="value2")
OR for multiple tools:
TOOL_NEEDED: [tool1(args), tool2(args)]

CRITICAL: Use exact tool names from available tools list above."""


def _can_answer_directly(response: str) -> bool:
    """Check if response indicates direct answer capability."""
    return response.strip().startswith("DIRECT_RESPONSE:")


def _extract_direct_response(response: str) -> str:
    """Extract clean response from DIRECT_RESPONSE format."""
    return response.replace("DIRECT_RESPONSE:", "").strip()


def _extract_tool_calls(response: str) -> Optional[str]:
    """Extract tool calls from TOOL_NEEDED format."""
    if "TOOL_NEEDED:" in response:
        return response.split("TOOL_NEEDED:", 1)[1].strip()
    return None


def _task_complete(context, tool_results: List[Dict]) -> bool:
    """Determine if task is complete based on tool results and context."""
    if not tool_results:
        return False
    
    # Simple heuristic: if we got tool results, task is likely complete
    # More sophisticated logic can be added here
    return len(tool_results) > 0


@trace_node("reason")
async def reason(state: AgentState, llm: BaseLLM, tools: Optional[List[BaseTool]] = None, 
                prompt_fragments: Optional[Dict[str, str]] = None) -> AgentState:
    """Unified reasoning: analyze → decide → execute → complete."""
    
    context = state["context"]
    trace = state["trace"]
    user_input = context.current_input
    
    # Use pre-selected tools from state or fall back to all tools
    selected_tools = state.get("selected_tools", tools or [])
    
    # Build tool info
    if selected_tools:
        tool_descriptions = []
        for tool in selected_tools:
            tool_descriptions.append(f"{tool.name} ({tool.description})")
        tool_info = ", ".join(tool_descriptions)
    else:
        tool_info = "no tools"
    
    # Reasoning loop - continue until task complete
    max_iterations = 3
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        trace.add("reason", f"Reasoning iteration {iteration}")
        
        # Prepare reasoning prompt
        messages = list(context.messages)
        messages.append({"role": "user", "content": user_input})
        
        system_prompt = REASON_PROMPT.format(
            tool_names=tool_info,
            user_input=user_input,
            injection_point=prompt_fragments.get("injection_point", "") if prompt_fragments else ""
        )
        messages.insert(0, {"role": "system", "content": system_prompt})
        
        # Get reasoning decision
        llm_response = await llm.invoke(messages)
        context.add_message("assistant", llm_response)
        
        # Check if direct response
        if _can_answer_directly(llm_response):
            response_text = _extract_direct_response(llm_response)
            trace.add("reason", f"Direct response generated: {response_text[:50]}...")
            
            decision = ReasoningDecision(
                should_respond=True,
                response_text=response_text,
                task_complete=True
            )
            
            return {
                "context": context,
                "reasoning_decision": decision,
                "last_node_output": response_text
            }
        
        # Extract and execute tool calls
        tool_call_str = _extract_tool_calls(llm_response)
        if tool_call_str:
            trace.add("reason", f"Tool calls identified: {tool_call_str}")
            
            # Validate tool calls
            if selected_tools:
                validated_response = validate_tools(tool_call_str, selected_tools)
                if validated_response != tool_call_str:
                    tool_call_str = validated_response
            
            # Parse and execute tools
            tool_call = parse_tool_call(tool_call_str)
            tool_results = []
            
            if tool_call:
                if isinstance(tool_call, MultiToolCall):
                    # Execute parallel tools
                    tool_calls_for_execution = [(call.name, call.args) for call in tool_call.calls]
                    await execute_parallel_tools(tool_calls_for_execution, selected_tools, context)
                    tool_results = context.tool_results if hasattr(context, 'tool_results') else []
                    
                elif isinstance(tool_call, ToolCall):
                    # Execute single tool
                    tool_name, parsed_args, tool_output = await execute_single_tool(
                        tool_call.name, tool_call.args, selected_tools
                    )
                    context.add_message("system", str(tool_output))
                    context.add_tool_result(tool_name, parsed_args, tool_output)
                    tool_results = [{"tool": tool_name, "output": tool_output}]
                
                trace.add("reason", f"Executed {len(tool_results)} tools")
            
            # Check if task is complete
            if _task_complete(context, tool_results):
                trace.add("reason", "Task complete after tool execution")
                
                # Generate final response incorporating tool results
                final_messages = list(context.messages)
                final_messages.insert(0, {"role": "system", "content": 
                    "Generate a clear, helpful response incorporating the tool results. "
                    "Be conversational and natural - speak directly to the user."
                })
                
                final_response = await llm.invoke(final_messages)
                context.add_message("assistant", final_response)
                
                decision = ReasoningDecision(
                    should_respond=True,
                    response_text=final_response,
                    task_complete=True
                )
                
                return {
                    "context": context,
                    "reasoning_decision": decision,
                    "last_node_output": final_response
                }
            
            # Continue reasoning with tool results
            continue
        
        # No tools identified and no direct response - fallback
        trace.add("reason", "No clear action identified, generating fallback response")
        
        decision = ReasoningDecision(
            should_respond=True,
            response_text=llm_response,
            task_complete=True
        )
        
        return {
            "context": context,
            "reasoning_decision": decision,
            "last_node_output": llm_response
        }
    
    # Max iterations reached
    trace.add("reason", f"Max iterations ({max_iterations}) reached")
    
    decision = ReasoningDecision(
        should_respond=True,
        response_text="I've reached the maximum reasoning iterations. Let me provide what I can determine so far.",
        task_complete=True
    )
    
    return {
        "context": context,
        "reasoning_decision": decision,
        "last_node_output": decision.response_text
    }