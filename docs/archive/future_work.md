# Future Ideas & Improvements

## LLM-Driven Context Compression

**Problem**: Long horizon tasks accumulate massive amounts of tool results. Current approach either:
- Dumps raw results → respond node overwhelmed with noise
- Uses brittle heuristics (format_agent, arbitrary limits) → loses important context

**Insight**: The reasoning LLM is already analyzing tool results to make decisions. Extend it to simultaneously compress/curate results in the same pass.

**Vision**:
```python
# Extended reasoning output
{
  "reasoning": "standard decision making",
  "tool_calls": [...],
  "key_insights": "2-3 sentence summary of important findings from tool results",
  "relevance_score": "high|medium|low",
  "synthesis": "how this connects to previous iterations and overall goal"
}
```

**Benefits**:
- Zero heuristics - pure intelligence-driven compression
- Context-aware relevance filtering (LLM understands the goal)
- Natural language synthesis vs raw data dumps
- Coherent narrative maintained across iterations
- Respond node gets pre-curated, high-quality context

**Technical Challenges**:
- Timing: when to compress (current cycle vs next cycle)
- Multi-tool handling: compress individually or batch
- State schema: store raw + compressed, or just compressed?
- Prompt complexity: fast/deep modes + compression instructions
- JSON extraction reliability with additional fields
- Notification UX: when to show compressed summaries

**Implementation Approach**:
1. Extend reasoning response schema
2. Store compressed insights in iterations instead of raw dumps
3. Update respond node to use curated iteration context
4. Consider background compression for tool-heavy iterations

**Why This Matters**:
Smart agent = smart context management. This moves from "dump everything" to "curate intelligently", which is crucial for complex, multi-step reasoning tasks.

**Status**: Research/design phase. Needs architectural thinking before implementation.