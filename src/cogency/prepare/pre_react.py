"""Pre-ReAct node - memory extraction and tool filtering."""
from typing import List

from cogency.llm import BaseLLM
from cogency.tools.base import BaseTool
from cogency.memory.base import BaseMemory
from cogency.common.types import AgentState
from cogency.utils.tracing import trace_node
from cogency.prepare.memory import should_extract_memory, save_extracted_memory
from cogency.prepare.tools import create_registry_lite, filter_tools_by_exclusion, prepare_tools_for_react
from cogency.prepare.extract import extract_memory_and_filter_tools


@trace_node("pre_react")
async def pre_react_node(state: AgentState, *, llm: BaseLLM, tools: List[BaseTool], memory: BaseMemory) -> AgentState:
    """Pre-ReAct: Extract memory + filter tools, then prep for ReAct."""
    query = state["query"]
    context = state["context"]
    user_id = getattr(context, 'user_id', 'default')
    
    # Quick heuristic check for memory extraction
    needs_memory_extract = should_extract_memory(query)
    
    # Use LLM for dual flow if many tools OR memory needs extraction
    if (tools and len(tools) > 5) or needs_memory_extract:
        # Create registry lite (names + descriptions only)
        registry_lite = create_registry_lite(tools)
        
        # Single LLM call for memory extraction + tool filtering
        result = await extract_memory_and_filter_tools(query, registry_lite, llm)
        
        # Chain 1: Save extracted memory if not null/empty
        await save_extracted_memory(
            result["memory_summary"], 
            memory, 
            user_id,
            tags=result.get("tags", []),
            memory_type=result.get("memory_type", "fact")
        )
        
        # Chain 2: Filter tools by exclusion (conservative)
        filtered_tools = filter_tools_by_exclusion(tools, result["excluded_tools"])
        
        # TODO: Log reasoning trace for debugging - could be visualized or embedded downstream
    else:
        # Simple case: just use first few tools
        filtered_tools = tools[:3] if tools else []
    
    # Chain 3: Prepare tools for ReAct (remove memorize, keep recall)
    # Add zero-tools fallback to prevent react_loop breaks
    prepared_tools = prepare_tools_for_react(filtered_tools)
    state["selected_tools"] = prepared_tools if prepared_tools else tools[:1]  # Fallback to first tool
    
    return state