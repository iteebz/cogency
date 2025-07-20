"""Preprocess node - routing, memory extraction, tool filtering."""
from typing import List, Optional, Dict, Any

from cogency.llm import BaseLLM
from cogency.tools.base import BaseTool
from cogency.memory.core import MemoryBackend
from cogency.types import AgentState
from cogency.tracing import trace_node
from cogency.memory.prepare import save_extracted_memory
from cogency.memory.extract import extract_memory_and_filter_tools
# Removed ceremony - inlined simple operations
from cogency.messaging import AgentMessenger
from cogency.reasoning.adaptive import AdaptiveController, StoppingCriteria
# Eliminated import ceremony - using simple strings




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
    
    # Pre-React phases will stream via MEMORIZE and TOOLING messages below
    
    # Use LLM for intelligent analysis when we have tools (memory + complexity + filtering)
    if tools and len(tools) > 0:
        # Create registry lite (names + descriptions only) - inline, no ceremony
        registry_entries = []
        for tool in tools:
            entry = f"- {tool.name}: {tool.description}"
            try:
                schema = tool.get_schema()
                if schema:
                    entry += f"\n  Schema: {schema}"
            except (AttributeError, NotImplementedError):
                pass
            registry_entries.append(entry)
        registry_lite = "\n\n".join(registry_entries)
        
        # Single LLM call for memory extraction + tool filtering + complexity analysis
        result = await extract_memory_and_filter_tools(query, registry_lite, llm)
        
        # Extract LLM-provided complexity
        complexity = result["complexity"]
        
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
        
        # Chain 2: Filter tools by exclusion (conservative) - inline, no ceremony
        excluded_names = set(result["excluded_tools"]) if result["excluded_tools"] else set()
        filtered_tools = [tool for tool in tools if tool.name not in excluded_names]
        
        # Stream tool filtering
        if streaming_callback:
            selected_tool_names = [tool.name for tool in filtered_tools]
            await AgentMessenger.tooling(
                streaming_callback,
                selected_tool_names
            )
    else:
        # Simple case: use all tools (no filtering), basic complexity
        filtered_tools = tools
        complexity = 0.3  # Simple fallback for no-tool scenarios
        
        # Always stream tool selection
        if streaming_callback and tools:
            selected_tool_names = [tool.name for tool in filtered_tools]
            await AgentMessenger.tooling(
                streaming_callback,
                selected_tool_names
            )
    
    # Chain 3: Prepare tools for ReAct (remove memorize, keep recall) - inline, no ceremony
    prepared_tools = [tool for tool in filtered_tools if tool.name != 'memorize']
    state["selected_tools"] = prepared_tools if prepared_tools else tools  # Use all tools as fallback
    
    # Chain 4: Initialize adaptive reasoning controller
    criteria = StoppingCriteria()
    criteria.max_iterations = max(3, int(complexity * 10))  # 3-10 iterations based on complexity
    
    controller = AdaptiveController(criteria)
    controller.start_reasoning()
    
    state["adaptive_controller"] = controller
    state["complexity_score"] = complexity
    
    # Chain 5: Use LLM routing decision - respond node ALWAYS handles response generation
    if tools and len(tools) > 0:
        # Use LLM's intelligent routing decision
        bypass_decision = result.get("bypass_react", False)
        if bypass_decision:
            state["next_node"] = "respond"  # Skip ReAct, go straight to respond
        else:
            state["next_node"] = "reason"   # Use ReAct workflow
    else:
        # No tools available, respond directly
        state["next_node"] = "respond"
    
    return state


