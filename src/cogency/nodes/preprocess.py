"""Preprocess node - routing, memory extraction, tool filtering."""
from typing import List, Optional, Dict, Any

from cogency.llm import BaseLLM
from cogency.tools.base import BaseTool
from cogency.memory.core import MemoryBackend
from cogency.types import AgentState
from cogency.tracing import trace_node
from cogency.memory.prepare import save_extracted_memory
from cogency.utils.json import extract_json
# Removed ceremony - inlined simple operations
from cogency.messaging import AgentMessenger
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
        
        # Add trace for tool registry (dev debugging)
        if state.get("trace"):
            state["trace"].add("preprocess", f"Built tool registry with {len(tools)} tools", {"tool_count": len(tools), "tool_names": [t.name for t in tools]})
        
        # Single LLM call: routing + memory + tool selection
        prompt = f"""Query: "{query}"

MEMORY: Extract if user shares facts about themselves or explicitly asks to remember something.
- Name, job, preferences, personal context → extract 
- "Remember that..." → extract
- Questions, general chat → null

ROUTING: Decide if you need tools or can respond directly.
- If you might need ANY tools from the available toolkit → respond_directly: false
- Only if you're 100% certain you need NO tools → respond_directly: true

TOOL SELECTION: Select tools you might need. You have full freedom to decide.
Available tools: {registry_lite}

Return JSON:
{{
  "memory": "summary" | null,
  "tags": ["tag1", "tag2"] | null,
  "memory_type": "fact",
  "respond_directly": true | false,
  "selected_tools": ["tool1", "tool2"] | [],
  "reasoning": "brief explanation"
}}"""

        response = await llm.invoke([{"role": "user", "content": prompt}])
        
        fallback = {
            "memory": None, 
            "tags": [], 
            "memory_type": "fact", 
            "respond_directly": True,
            "selected_tools": [],
            "reasoning": ""
        }
        result = extract_json(response, fallback)
        
        # Chain 1: Save extracted memory if not null/empty
        if result.get("memory") and streaming_callback:
            # Stream memory extraction
            memory_content = result['memory']
            display_content = f"{memory_content[:50]}..." if len(memory_content) > 50 else memory_content
            await AgentMessenger.memory_operation(streaming_callback, "save", display_content)
        
        if result.get("memory"):
            await save_extracted_memory(
                result["memory"], 
                memory, 
                user_id,
                tags=result.get("tags", []),
                memory_type=result.get("memory_type", "fact")
            )
        
        # Chain 2: Filter tools based on LLM selection
        if result.get("selected_tools"):
            selected_names = set(result["selected_tools"])
            filtered_tools = [tool for tool in tools if tool.name in selected_names]
        else:
            filtered_tools = tools  # Fallback to all tools
        
        # Stream tool selection - show off the intelligence
        if streaming_callback and filtered_tools:
            if len(filtered_tools) < len(tools):
                # Show smart filtering
                tool_names = [f"{t.emoji} {t.name}" for t in filtered_tools]
                await AgentMessenger.tool_selection(streaming_callback, tool_names, filtered=True)
            elif len(filtered_tools) > 1:
                # Show tools being prepared for ReAct
                tool_names = [f"{t.emoji} {t.name}" for t in filtered_tools]
                await AgentMessenger.tool_selection(streaming_callback, tool_names, filtered=False)
    else:
        # Simple case: use all tools, respond directly
        filtered_tools = tools
        result = {"respond_directly": True}
        
        # Always stream tool selection
        # Tool selection is now silent - no ceremony
    
    # Chain 3: Prepare tools for ReAct (remove memorize, keep recall) - inline, no ceremony
    prepared_tools = [tool for tool in filtered_tools if tool.name != 'memorize']
    state["selected_tools"] = prepared_tools if prepared_tools else tools  # Use all tools as fallback
    
    # Simple iteration tracking
    state["max_iterations"] = 5
    state["current_iteration"] = 0
    
    # Chain 5: Simple routing decision 
    if tools and len(tools) > 0:
        if result.get("respond_directly", True):
            state["next_node"] = "respond"  # Direct response
        else:
            state["next_node"] = "reason"   # Use ReAct workflow
    else:
        # No tools available, respond directly
        state["next_node"] = "respond"
    
    return state


