"""Preprocess node - routing, memory extraction, tool filtering."""
from typing import List, Optional, Dict, Any

from cogency.llm import BaseLLM
from cogency.tools.base import BaseTool
from cogency.memory.core import MemoryBackend
from cogency.common.types import AgentState
from cogency.utils.tracing import trace_node
from cogency.prepare.memory import should_extract_memory, save_extracted_memory
from cogency.prepare.extract import extract_memory_and_filter_tools
from cogency.prepare.tools import create_registry_lite, filter_tools_by_exclusion, prepare_tools_for_react
from cogency.streaming.messaging import AgentMessenger
from cogency.reasoning.adaptive import ReasonController, StoppingCriteria
from cogency.reasoning.complexity import analyze_query_complexity




@trace_node("preprocess")
async def preprocess_node(state: AgentState, *, llm: BaseLLM, tools: List[BaseTool], memory: MemoryBackend, system_prompt: str = None, config: Optional[Dict] = None) -> AgentState:
    """Preprocess: routing decisions, memory extraction, tool selection."""
    query = state["query"]
    context = state["context"]
    user_id = getattr(context, 'user_id', 'default')
    
    # Get streaming callback if available
    streaming_callback = None
    if config and "configurable" in config:
        streaming_callback = config["configurable"].get("streaming_callback")
    
    # Quick heuristic check for memory extraction
    needs_memory_extract = should_extract_memory(query)
    
    # Pre-React phases will stream via MEMORIZE and TOOLING messages below
    
    # Use LLM for dual flow if many tools OR memory needs extraction
    if (tools and len(tools) > 5) or needs_memory_extract:
        # Create registry lite (names + descriptions only)
        registry_lite = create_registry_lite(tools)
        
        # Single LLM call for memory extraction + tool filtering
        result = await extract_memory_and_filter_tools(query, registry_lite, llm)
        
        # Chain 1: Save extracted memory if not null/empty
        if result["memory_summary"] and streaming_callback:
            # Stream memory extraction
            await AgentMessenger.memorize(
                streaming_callback,
                f"Saving extracted insight: {result['memory_summary'][:50]}..." if len(result['memory_summary']) > 50 else result['memory_summary']
            )
        
        if result["memory_summary"]:
            await save_extracted_memory(
                result["memory_summary"], 
                memory, 
                user_id,
                tags=result.get("tags", []),
                memory_type=result.get("memory_type", "fact")
            )
        
        # Chain 2: Filter tools by exclusion (conservative)
        filtered_tools = filter_tools_by_exclusion(tools, result["excluded_tools"])
        
        # Stream tool filtering
        if streaming_callback:
            selected_tool_names = [tool.name for tool in filtered_tools]
            await AgentMessenger.tooling(
                streaming_callback,
                selected_tool_names
            )
    else:
        # Simple case: use all tools (no filtering)
        filtered_tools = tools
        
        # Always stream tool selection
        if streaming_callback and tools:
            selected_tool_names = [tool.name for tool in filtered_tools]
            await AgentMessenger.tooling(
                streaming_callback,
                selected_tool_names
            )
    
    # Chain 3: Prepare tools for ReAct (remove memorize, keep recall)
    # Add zero-tools fallback to prevent react_loop breaks
    prepared_tools = prepare_tools_for_react(filtered_tools)
    state["selected_tools"] = prepared_tools if prepared_tools else tools  # Use all tools as fallback
    
    # Chain 4: Initialize adaptive reasoning controller
    complexity = analyze_query_complexity(query, len(prepared_tools))
    criteria = StoppingCriteria()
    criteria.max_iterations = max(3, int(complexity * 10))  # 3-10 iterations based on complexity
    
    controller = ReasonController(criteria)
    controller.start_reasoning()
    
    state["adaptive_controller"] = controller
    state["complexity_score"] = complexity
    
    # Chain 5: Direct response detection for simple queries
    if _should_bypass_react(query, prepared_tools):
        state["next_node"] = "respond"
        state["direct_response_bypass"] = True
    else:
        state["next_node"] = "reason"
        state["direct_response_bypass"] = False
    
    return state


def _should_bypass_react(query: str, tools: List[BaseTool]) -> bool:
    """Heuristic to detect if query can be answered directly without tools."""
    query_lower = query.lower()
    
    # Simple conversational queries
    simple_patterns = [
        "hello", "hi", "thank you", "thanks", "bye", "goodbye",
        "how are you", "what are you", "who are you"
    ]
    
    # Questions that clearly don't need tools
    no_tool_patterns = [
        "what is", "define", "explain", "tell me about"
    ]
    
    # If no tools available, must respond directly
    if not tools:
        return True
    
    # Check for simple patterns
    if any(pattern in query_lower for pattern in simple_patterns):
        return True
    
    # Short queries under 10 words that don't seem to need tools
    if len(query.split()) < 10 and any(pattern in query_lower for pattern in no_tool_patterns):
        return True
    
    return False