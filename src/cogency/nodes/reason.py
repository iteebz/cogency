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
    return response.strip().startswith("DIRECT_RESPONSE:")

def _extract_direct_response(response: str) -> str:
    return response.replace("DIRECT_RESPONSE:", "").strip()

def _extract_tool_calls(response: str) -> Optional[str]:
    if "TOOL_NEEDED:" in response:
        return response.split("TOOL_NEEDED:", 1)[1].strip()
    return None

def _task_complete(context, tool_results: List[Dict]) -> bool:
    return len(tool_results) > 0 if tool_results else False

def _task_complete_with_results(context, execution_results: Dict[str, Any]) -> bool:
    """Check if task is complete based on execution results.
    
    Task is complete if:
    1. At least one tool executed successfully, OR
    2. All tools failed but we have enough context to provide a response
    """
    if not execution_results:
        return False
    
    # If we have successful results, task is complete
    if execution_results.get("success") and execution_results.get("results"):
        return True
    
    # If all tools failed, we can still complete with error context
    if execution_results.get("errors") and len(execution_results.get("errors", [])) > 0:
        return True
    
    return False


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
            
            return {
                "context": context,
                "reasoning_decision": ReasoningDecision(should_respond=True, response_text=response_text, task_complete=True),
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
            execution_results = {}
            
            if tool_call:
                if isinstance(tool_call, MultiToolCall):
                    # Execute parallel tools with robust error handling
                    tool_calls_for_execution = [(call.name, call.args) for call in tool_call.calls]
                    execution_results = await execute_parallel_tools(tool_calls_for_execution, selected_tools, context)
                    
                elif isinstance(tool_call, ToolCall):
                    # Execute single tool with structured error handling
                    tool_name, parsed_args, tool_output = await execute_single_tool(
                        tool_call.name, tool_call.args, selected_tools
                    )
                    
                    if isinstance(tool_output, dict) and tool_output.get("success") is False:
                        # Tool failed - add error to context
                        error_msg = f"Tool '{tool_name}' failed: {tool_output.get('error', 'Unknown error')}"
                        context.add_message("system", error_msg)
                        execution_results = {
                            "success": False,
                            "errors": [{
                                "tool_name": tool_name,
                                "args": parsed_args,
                                "error": tool_output.get("error"),
                                "error_type": tool_output.get("error_type")
                            }],
                            "results": [],
                            "summary": f"Tool {tool_name} failed"
                        }
                    else:
                        # Tool succeeded
                        result = tool_output.get("result") if isinstance(tool_output, dict) else tool_output
                        context.add_message("system", str(result))
                        context.add_tool_result(tool_name, parsed_args, result)
                        execution_results = {
                            "success": True,
                            "results": [{"tool_name": tool_name, "args": parsed_args, "result": result}],
                            "errors": [],
                            "summary": f"Tool {tool_name} executed successfully"
                        }
                
                trace.add("reason", f"Tool execution summary: {execution_results.get('summary', 'No summary')}")
            
            # Check if task is complete based on execution results
            if _task_complete_with_results(context, execution_results):
                trace.add("reason", "Task complete after tool execution")
                
                # Generate final response incorporating tool results and handling errors
                final_messages = list(context.messages)
                
                # Create context-aware system prompt based on execution results
                if execution_results.get("success"):
                    system_prompt = (
                        "Generate a clear, helpful response incorporating the successful tool results. "
                        "Be conversational and natural - speak directly to the user."
                    )
                else:
                    system_prompt = (
                        "Some tools failed during execution. Generate a helpful response that: "
                        "1. Acknowledges what went wrong "
                        "2. Provides alternative solutions or suggestions "
                        "3. Remains helpful and conversational "
                        "4. Uses any partial results that may be available"
                    )
                
                final_messages.insert(0, {"role": "system", "content": system_prompt})
                
                final_response = await llm.invoke(final_messages)
                context.add_message("assistant", final_response)
                
                return {
                    "context": context,
                    "reasoning_decision": ReasoningDecision(should_respond=True, response_text=final_response, task_complete=True),
                    "last_node_output": final_response
                }
            
            # Continue reasoning with tool results
            continue
        
        # No tools identified and no direct response - fallback
        trace.add("reason", "No clear action identified, generating fallback response")
        
        return {
            "context": context,
            "reasoning_decision": ReasoningDecision(should_respond=True, response_text=llm_response, task_complete=True),
            "last_node_output": llm_response
        }
    
    # Max iterations reached
    trace.add("reason", f"Max iterations ({max_iterations}) reached")
    fallback_text = "I've reached the maximum reasoning iterations. Let me provide what I can determine so far."
    
    return {
        "context": context,
        "reasoning_decision": ReasoningDecision(should_respond=True, response_text=fallback_text, task_complete=True),
        "last_node_output": fallback_text
    }