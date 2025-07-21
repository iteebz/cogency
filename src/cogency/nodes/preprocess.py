"""Preprocess node - routing, memory extraction, tool filtering."""
from typing import List, Optional, Dict, Any

from cogency.llm import BaseLLM
from cogency.tools.base import BaseTool
from cogency.memory.core import MemoryBackend
from cogency.state import AgentState
from cogency.output import emoji

from cogency.memory.prepare import save_extracted_memory
from cogency.utils.json import extract_json




async def preprocess_node(state: AgentState, *, llm: BaseLLM, tools: List[BaseTool], memory: MemoryBackend, system_prompt: str = None, config: Optional[Dict] = None) -> AgentState:
    """Preprocess: routing decisions, memory extraction, tool selection."""
    query = state["query"]
    context = state["context"]
    user_id = getattr(context, 'user_id', 'default')
    
    
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
        await state.output.send("trace", f"Built tool registry with {len(tools)} tools", node="preprocess", tool_count=len(tools), tool_names=[t.name for t in tools])
        
        # Single LLM call: routing + memory + tool selection + complexity analysis
        prompt = f"""Query: "{query}"

MEMORY: Extract if user shares personal facts or says "remember that...". Otherwise null.

ROUTING: Need tools → respond_directly: false. Can answer directly → respond_directly: true.

COMPLEXITY: Fast = lookup/search/retrieval. Deep = analysis/synthesis/multi-step.

TOOLS: Select what you need from: {registry_lite}

JSON:
{{
  "memory": "summary" | null,
  "tags": ["tag1", "tag2"] | null,
  "memory_type": "fact",
  "respond_directly": true | false,
  "react_mode": "fast" | "deep",
  "selected_tools": ["tool1", "tool2"] | [],
  "reasoning": "brief explanation"
}}"""

        response = await llm.run([{"role": "user", "content": prompt}])
        
        fallback = {
            "memory": None, 
            "tags": [], 
            "memory_type": "fact", 
            "respond_directly": True,
            "react_mode": "fast",
            "selected_tools": [],
            "reasoning": ""
        }
        result = extract_json(response, fallback)
        
        # Chain 1: Save extracted memory if not null/empty and memory is enabled
        if memory and result.get("memory"):
            # Stream memory extraction using clean API
            memory_content = result['memory']
            display_content = f"{memory_content[:50]}..." if len(memory_content) > 50 else memory_content
            memory_emoji = emoji['memory']
            await state.output.send("update", f"{memory_emoji} {display_content}")
            
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
        
        # Stream tool selection using clean API
        if filtered_tools:
            if len(filtered_tools) < len(tools):
                # Show smart filtering
                tool_names = [f"{t.emoji} {t.name}" for t in filtered_tools]
                tool_emoji = emoji['trace']
                await state.output.send("update", f"{tool_emoji} Tools: {', '.join([t.name for t in filtered_tools])}")
            elif len(filtered_tools) > 1:
                # Show tools being prepared for ReAct
                tool_names = [f"{t.emoji} {t.name}" for t in filtered_tools]
                tool_emoji = emoji['trace']
                await state.output.send("update", f"{tool_emoji} Tools: {', '.join([t.name for t in filtered_tools])}")
    else:
        # Simple case: use all tools, respond directly
        filtered_tools = tools
        result = {"respond_directly": True}
        
        # Always stream tool selection
        # Tool selection is now silent - no ceremony
    
    # Chain 3: Prepare tools for ReAct (remove memorize, keep recall) - inline, no ceremony
    prepared_tools = [tool for tool in filtered_tools if tool.name != 'memorize']
    selected_tools = prepared_tools if prepared_tools else tools  # Use all tools as fallback
    
    # Chain 5: 3-way routing decision 
    if tools and len(tools) > 0:
        if result.get("respond_directly", True):
            next_node = "respond"  # Direct response
        else:
            next_node = "reason"   # Use ReAct workflow
            react_mode = result.get("react_mode", "fast")  # Cognitive complexity
            
            # Trace complexity assessment and mode decision
            complexity = result.get("complexity_level", "unknown")
            await state.output.send("trace", f"Complexity: {complexity} → {react_mode.upper()} mode selected", node="preprocess")
    else:
        # No tools available, respond directly
        next_node = "respond"
    
    # Update flow state - ephemeral workflow data
    state["selected_tools"] = selected_tools
    state["react_mode"] = result.get("react_mode", "fast")
    state["max_iterations"] = 5
    state["current_iteration"] = 0
    state["next_node"] = next_node
    
    return state


