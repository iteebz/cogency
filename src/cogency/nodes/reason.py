"""Unified reasoning node - THINK+PLAN+REFLECT merged into pure cognition."""
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


def _estimate_query_complexity(user_input: str, tool_count: int) -> float:
    """Estimate query complexity for adaptive iteration control."""
    complexity_score = 0.0
    
    # Length factor (longer queries tend to be more complex)
    complexity_score += min(0.3, len(user_input) / 300)  # Reduced denominator for more impact
    
    # Keyword complexity indicators with higher weights
    complex_keywords = ['analyze', 'compare', 'evaluate', 'research', 'investigate', 'comprehensive', 'detailed', 'implications', 'trade-offs', 'performance', 'frameworks']
    simple_keywords = ['what', 'when', 'where', 'who', 'define', 'explain', 'is', 'are']
    
    complex_count = sum(1 for keyword in complex_keywords if keyword in user_input.lower())
    simple_count = sum(1 for keyword in simple_keywords if keyword in user_input.lower())
    
    # Higher weight for complex keywords
    complexity_score += min(0.4, complex_count * 0.15)
    complexity_score -= min(0.2, simple_count * 0.05)
    
    # Tool availability factor (more tools = potentially more complex reasoning)
    complexity_score += min(0.2, tool_count / 15)  # Reduced denominator for more impact
    
    # Question marks and conjunctions (multiple questions = complexity)
    complexity_score += min(0.1, user_input.count('?') * 0.05)
    complexity_score += min(0.15, user_input.count(' and ') * 0.05)  # Higher weight for conjunctions
    
    # Multiple sentences indicate complexity
    sentence_count = max(1, user_input.count('.') + user_input.count('!') + user_input.count('?'))
    if sentence_count > 1:
        complexity_score += min(0.2, sentence_count * 0.05)
    
    return max(0.1, min(1.0, complexity_score))


@trace_node("reason")
async def reason(state: AgentState, llm: BaseLLM, tools: Optional[List[BaseTool]] = None, 
                prompt_fragments: Optional[Dict[str, str]] = None) -> AgentState:
    """Unified reasoning: analyze → decide → execute → complete with adaptive depth control."""
    
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
    
    # Initialize adaptive reasoning controller
    complexity = _estimate_query_complexity(user_input, len(selected_tools))
    criteria = StoppingCriteria()
    criteria.max_iterations = criteria.max_iterations if complexity < 0.7 else min(criteria.max_iterations + 2, 8)
    
    controller = AdaptiveReasoningController(criteria)
    controller.start_reasoning()
    
    from cogency.utils.explanation import ExplanationGenerator, ExplanationLevel, ExplanationContext
    explainer = ExplanationGenerator(ExplanationLevel.CONCISE)
    
    context_info = ExplanationContext(
        user_query=user_input,
        tools_available=[tool.name for tool in selected_tools] if selected_tools else [],
        reasoning_depth=criteria.max_iterations,
        execution_time=0.0,
        success=True
    )
    
    explanation = explainer.explain_reasoning_start(context_info)
    trace.add("reason", f"Adaptive reasoning started - complexity: {complexity:.2f}, max_iterations: {criteria.max_iterations}", explanation=explanation)
    
    # Reasoning loop with adaptive control
    while True:
        iteration_start_time = time.time()
        
        # Check if we should continue reasoning
        should_continue, stopping_reason = controller.should_continue_reasoning(
            iteration_start_time=iteration_start_time
        )
        
        if not should_continue:
            explanation = explainer.explain_stopping_criteria(stopping_reason.value, {"total_time": time.time() - controller.metrics.start_time})
            trace.add("reason", f"Stopping reasoning: {stopping_reason.value}", explanation=explanation)
            break
        
        trace.add("reason", f"Reasoning iteration {controller.metrics.iteration + 1}")
        
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
            explanation = explainer.explain_reasoning_decision("direct_response", "I can answer this directly")
            trace.add("reason", f"Direct response generated: {response_text[:50]}...", explanation=explanation)
            
            # Update metrics and log completion
            iteration_time = time.time() - iteration_start_time
            controller.update_iteration_metrics({}, iteration_time)
            
            summary = controller.get_reasoning_summary()
            trace.add("reason", f"Reasoning completed - iterations: {summary['total_iterations']}, time: {summary['total_time']:.2f}s")
            
            return {
                "context": context,
                "reasoning_decision": ReasoningDecision(should_respond=True, response_text=response_text, task_complete=True),
                "last_node_output": response_text
            }
        
        # Extract and execute tool calls
        tool_call_str = _extract_tool_calls(llm_response)
        execution_results = {}
        
        if tool_call_str:
            trace.add("reason", f"Tool calls identified: {tool_call_str}")
            
            # Validate tool calls
            if selected_tools:
                validated_response = validate_tools(tool_call_str, selected_tools)
                if validated_response != tool_call_str:
                    tool_call_str = validated_response
            
            # Parse and execute tools
            tool_call = parse_tool_call(tool_call_str)
            
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
                            "summary": f"Tool {tool_name} failed",
                            "total_executed": 1,
                            "successful_count": 0,
                            "failed_count": 1
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
                            "summary": f"Tool {tool_name} executed successfully",
                            "total_executed": 1,
                            "successful_count": 1,
                            "failed_count": 0
                        }
                
                trace.add("reason", f"Tool execution summary: {execution_results.get('summary', 'No summary')}")
        
        # Update iteration metrics
        iteration_time = time.time() - iteration_start_time
        controller.update_iteration_metrics(execution_results, iteration_time)
        
        # Check if task is complete based on execution results
        if execution_results and _task_complete_with_results(context, execution_results):
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
            
            # Log completion summary
            summary = controller.get_reasoning_summary()
            trace.add("reason", f"Reasoning completed - iterations: {summary['total_iterations']}, time: {summary['total_time']:.2f}s, tools: {summary['total_tools_executed']}")
            
            return {
                "context": context,
                "reasoning_decision": ReasoningDecision(should_respond=True, response_text=final_response, task_complete=True),
                "last_node_output": final_response
            }
        
        # Check adaptive stopping criteria after each iteration
        should_continue, stopping_reason = controller.should_continue_reasoning(execution_results)
        
        if not should_continue:
            trace.add("reason", f"Adaptive stopping: {stopping_reason.value}")
            break
        
        # Continue reasoning with tool results
        
        # If no tools identified and no direct response, check if we should stop
        if not tool_call_str:
            trace.add("reason", "No clear action identified, checking stopping criteria")
            
            # Update metrics for iteration without tools
            iteration_time = time.time() - iteration_start_time
            controller.update_iteration_metrics({}, iteration_time)
            
            # Check if we should stop due to lack of progress
            should_continue, stopping_reason = controller.should_continue_reasoning()
            
            if not should_continue:
                trace.add("reason", f"Stopping due to: {stopping_reason.value}")
                summary = controller.get_reasoning_summary()
                trace.add("reason", f"Reasoning completed - iterations: {summary['total_iterations']}, time: {summary['total_time']:.2f}s")
                
                return {
                    "context": context,
                    "reasoning_decision": ReasoningDecision(should_respond=True, response_text=llm_response, task_complete=True),
                    "last_node_output": llm_response
                }
    
    # Loop ended due to stopping criteria
    summary = controller.get_reasoning_summary()
    trace.add("reason", f"Reasoning completed - iterations: {summary['total_iterations']}, time: {summary['total_time']:.2f}s")
    
    # Generate final response based on stopping reason
    if stopping_reason == StoppingReason.CONFIDENCE_THRESHOLD:
        fallback_text = "I've gathered sufficient information to provide a confident response."
    elif stopping_reason == StoppingReason.TIME_LIMIT:
        fallback_text = "I've reached the time limit for reasoning. Let me provide what I can determine so far."
    elif stopping_reason == StoppingReason.DIMINISHING_RETURNS:
        fallback_text = "I've explored the available options thoroughly. Here's my response based on the information gathered."
    else:
        fallback_text = f"I've completed my reasoning process. Here's my response based on the analysis."
    
    # Get the last LLM response or generate a fallback
    final_messages = list(context.messages)
    if final_messages:
        # Use the last assistant message as the response
        last_response = next((msg["content"] for msg in reversed(final_messages) if msg["role"] == "assistant"), fallback_text)
        return {
            "context": context,
            "reasoning_decision": ReasoningDecision(should_respond=True, response_text=last_response, task_complete=True),
            "last_node_output": last_response
        }
    
    return {
        "context": context,
        "reasoning_decision": ReasoningDecision(should_respond=True, response_text=fallback_text, task_complete=True),
        "last_node_output": fallback_text
    }