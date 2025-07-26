"""Preprocess node - routing, memory extraction, tool filtering."""

from typing import List, Optional

from cogency.memory.core import MemoryBackend
from cogency.memory.prepare import save_memory
from cogency.resilience import safe, unwrap
from cogency.services.llm import BaseLLM
from cogency.state import State
from cogency.tools.base import BaseTool
from cogency.tools.registry import build_registry
from cogency.types.preprocessed import Preprocessed
from cogency.utils.heuristics import is_simple_query
from cogency.utils.parsing import parse_json


@safe.checkpoint("preprocess")
async def preprocess(
    state: State,
    *,
    llm: BaseLLM,
    tools: List[BaseTool],
    memory: MemoryBackend,
    system_prompt: str = None,
    identity: Optional[str] = None,
) -> State:
    """Preprocess: routing decisions, memory extraction, tool selection."""
    query = state["query"]
    context = state["context"]
    user_id = getattr(context, "user_id", "default")

    # Pre-React phases will stream via MEMORIZE and TOOLING messages below

    # Use LLM for intelligent analysis when we have tools (memory + complexity + filtering)
    if tools and len(tools) > 0:
        registry_lite = build_registry(tools, lite=True)

        # Skip preprocessing state - no ceremony

        # Trace for dev debugging
        await state.output.trace(f"Built tool registry with {len(tools)} tools", node="preprocess")

        # Pragmatic heuristic: Simple queries likely don't need deep reasoning
        suggested_mode = "fast" if is_simple_query(query) else None

        # Single LLM call: routing + memory + tool selection + complexity analysis
        hint_section = (
            "\nHINT: This appears to be a simple query, consider fast mode."
            if suggested_mode == "fast"
            else ""
        )

        prompt_preprocess = f"""You are a preprocessing agent responsible for query classification before reasoning begins.

Query: "{query}"

JSON Response Format:
{{
  "memory": "extracted user fact relevant for persistence" | null,
  "tags": ["topical", "categories"] | null,
  "memory_type": "fact",
  "react_mode": "fast" | "deep", 
  "selected_tools": ["tool1", "tool2"] | [],
  "reasoning": "brief justification of complexity and tool choices"
}}{hint_section}

ANALYSIS FRAMEWORK:
🧠 MEMORY: Extract factual user statements worth remembering (goals, context, identity) or null
🎯 COMPLEXITY: Classify task complexity using concrete signals:
   - FAST: Single factual lookup, basic calculation, direct command, simple question
   - DEEP: Multiple sources needed, comparison/synthesis, creative generation, coding tasks

🔧 TOOLS: Select tools that directly address query's core execution needs:
{registry_lite}

FIELD DEFINITIONS:
- memory: Extractive facts from user ("building a React app", "lives in London") 
- tags: Interpretive categories for later use ("ai", "coding", "travel")
- selected_tools: Subset of available tools needed for likely execution
- reasoning: How you classified complexity and selected tools

Example:
```json
{{
  "memory": "User mentioned working on a monorepo project called Folio",
  "tags": ["coding", "architecture"], 
  "memory_type": "fact",
  "react_mode": "deep",
  "selected_tools": ["files", "search"],
  "reasoning": "Software architecture query requires multiple steps and file analysis"
}}
```"""

        # @safe.preprocess() auto-unwraps Results - clean boundary discipline
        llm_result = await llm.run([{"role": "user", "content": prompt_preprocess}])
        llm_response = unwrap(llm_result)  # Unwrap LLM Result first
        parsed_data = unwrap(parse_json(llm_response))
        result = Preprocessed(**parsed_data)

        # Chain 1: Save extracted memory if not null/empty and memory is enabled
        if memory and result.memory:
            # Stream memory extraction using clean API
            memory_content = result.memory
            # Clean memory summary - avoid awkward truncation
            if memory_content and len(memory_content) > 60:
                # Find a natural break point near 60 chars
                break_point = memory_content.rfind(" ", 40, 60)
                if break_point == -1:
                    break_point = 60
                output_content = f"{memory_content[:break_point]}..."
            else:
                output_content = memory_content
            await state.output.update(f"Saved: {output_content}")

            # Let @safe.preprocess() handle memory save errors
            if memory_content:
                await save_memory(
                    memory_content,
                    memory,
                    user_id,
                    tags=result.tags,
                    memory_type=result.memory_type,
                )

        # Chain 2: Filter tools based on LLM selection and determine respond_directly
        selected_tools = result.selected_tools
        if selected_tools is not None:  # LLM explicitly provided selected_tools
            if not selected_tools:  # LLM explicitly selected no tools
                filtered_tools = []
                # If LLM explicitly selected no tools, force respond_directly to True
                state["respond_directly"] = True
            else:
                selected_names = set(selected_tools)
                filtered_tools = [tool for tool in tools if tool.name in selected_names]
                # If tools are selected, respond_directly should be False
                state["respond_directly"] = False
        else:  # LLM did not provide selected_tools, fallback to all tools and default respond_directly
            filtered_tools = tools
            # If LLM didn't specify selected_tools, assume tools are needed, so respond_directly is False
            state["respond_directly"] = False

        # Stream tool selection as trace for debugging
        if filtered_tools:
            if len(filtered_tools) < len(tools):
                # Show smart filtering in traces
                await state.output.trace(
                    f"Selected tools: {', '.join([t.name for t in filtered_tools])}",
                    node="preprocess",
                )
            elif len(filtered_tools) > 1:
                # Show tools being prepared for ReAct in traces
                await state.output.trace(
                    f"Preparing tools: {', '.join([t.name for t in filtered_tools])}",
                    node="preprocess",
                )
    else:
        # Simple case: no tools available, respond directly
        filtered_tools = []  # No tools to filter if initial 'tools' list is empty
        state["respond_directly"] = True  # Force respond directly if no tools are available

        # Tool selection is now silent - no ceremony

    # Chain 3: Prepare tools for ReAct (remove memorize, keep recall) - inline, no ceremony
    prepared_tools = [tool for tool in filtered_tools if tool.name != "memorize"]
    selected_tools = (
        prepared_tools if prepared_tools else []
    )  # Use empty list if no tools selected/prepared

    # Update flow state - clean routing via respond_directly flag
    state["selected_tools"] = selected_tools
    state["react_mode"] = result.react_mode if "result" in locals() else "fast"
    state["iteration"] = 0

    return state
