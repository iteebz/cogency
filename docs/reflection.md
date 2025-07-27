# Intelligent Context Management & Reflection Framework

## Problem Statement

Current iteration tracking mixes concerns and lacks intelligent compression:
- Raw tool outputs overwhelm token limits in long-horizon tasks
- Action "fingerprinting" is complex ceremony solving the wrong problem  
- No systematic way to extract learnings from tool executions
- Context fed to LLM lacks relevance-aware curation
- Debugging requires reconstructing what actually happened from fragments

## Solution: Two-Layer Architecture

### Layer 1: Source of Truth (Rich Iteration Records)
```python
iteration = {
    "iteration": int,
    "timestamp": datetime,
    "mode": "fast" | "deep",
    "tool_calls": [
        {
            "tool": str,
            "params": dict,
            "raw_output": str,  # Truncated to ~1000 chars for debugging
            "outcome": "success" | "failure" | "timeout" | "error",
            "execution_time": float,
            "cost": {"tokens": int, "time": float},
            "tool_selection_rationale": str,  # Why this tool vs others
            # LLM-generated intelligent compression ↓
            "insights": str,  # 1-2 sentences: key findings relevant to goal
            "learning": str,  # What this teaches us about approach/strategy  
            "relevance": "high" | "medium" | "low",  # To current goal
            "next_suggested_actions": str,  # Forward momentum from learnings
        }
    ],
    # Iteration-level synthesis ↓
    "synthesis": str,  # How this iteration advances overall goal
    "progress_assessment": "advancing" | "stuck" | "regressing",
    "user_feedback": str,  # Human corrections during execution
}
```

### Layer 2: Prompt Context (Compressed Reasoning History)
```python
reasoning_context = [
    "searched 'python tutorial' → found 3 results, too general for advanced debugging",
    "read logs/error.log → file empty, suggests logging not configured", 
    "searched 'flask production logging' → found setup docs, learned about werkzeug config"
]
```

## Key Design Decisions

**1. LLM-Driven Compression**
- Reasoning LLM generates `insights` + `learning` during tool result analysis
- Context-aware relevance scoring based on current goal
- Natural language synthesis vs brittle heuristics

**2. Tool-Level Granularity**
- Each tool call gets individual compression (different tools → different learnings)
- Iteration-level synthesis ties tools together
- Enables precise debugging of which tool provided what insight

**3. Immediate Compression Timing**
- Compression happens within same reasoning cycle that processes tool results
- Prevents off-by-one context lag
- LLM has full context for relevance assessment

**4. Storage Strategy**
- Store both raw (truncated) + compressed for debugging
- Rich iteration records for development/debugging
- Compressed context for LLM prompting

**5. Context Management**
- Relevance-ranked context filtering (`high`/`medium`/`low`)
- Chronological ordering within relevance tiers
- Dynamic context window based on token limits

## Loop Prevention Strategy

**Primary:** Reflection-based prevention through compressed learnings
- Clear context about what was tried and why it failed
- Explicit learnings about approach effectiveness
- Forward momentum through suggested next actions

**Fallback:** Simple stuck detection
- Track `progress_assessment` over recent iterations
- If `stuck` or `regressing` for 3+ iterations → trigger recovery prompt
- No complex fingerprinting - just pattern recognition

## Implementation Phases

**Phase 1: Schema Migration**
- Replace fingerprinting with readable action summaries
- Implement two-layer storage architecture
- Add basic compression fields

**Phase 2: Intelligent Compression**
- Extend reasoning prompts to extract insights/learnings
- Implement relevance-based context filtering
- Add cost/performance tracking

**Phase 3: Optimization**
- Batch compression for efficiency
- Optional compression for low-stakes tool calls
- Advanced context management strategies

## Principles

**Simplicity First:** Push complexity into LLM reasoning, not code architecture
**Debuggability:** Always maintain source of truth with raw data
**Extensibility:** Two-layer design allows future enhancements without breaking changes
**Cost Awareness:** Track and optimize for token usage and execution time

## Out of Scope (v2+)

- Semantic memory stores / vector databases
- Multi-agent workflows and explicit cognitive operators
- Complex planning and hypothesis management frameworks  
- Cross-task continuity and declarative knowledge systems

**Philosophy:** Nail the core intelligent context management first. Advanced reasoning primitives can be layered on top of this foundation.