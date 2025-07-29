# State Management Schema - Canonical Specification

**PRINCIPLE**: This document is the definitive specification. State implementation must match exactly.

## Semantic Context Summarization Architecture

### Core Insight
Instead of complex per-tool compression, we maintain a **living semantic summary** that gets smarter over time. The LLM updates 5 key fields each iteration, providing semantic understanding vs mechanical truncation.

## State Schema

```python
@dataclass 
class State:
    # Core execution context
    query: str
    user_id: str = "default"
    messages: List[Dict[str, str]] = field(default_factory=list)
    
    # Flow control  
    iteration: int = 0
    depth: int = DEFAULT_MAX_DEPTH
    react_mode: str = "fast"
    stop_reason: Optional[str] = None
    
    # Tool execution
    selected_tools: List[Any] = field(default_factory=list)
    tool_calls: List[Any] = field(default_factory=list)
    result: Any = None
    
    # Action history (rich records for debugging)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    attempts: List[Any] = field(default_factory=list)  # Legacy - unused
    current_approach: str = "initial"
    
    # SEMANTIC CONTEXT SUMMARIZATION - The canonical solution
    situation_summary: Dict[str, str] = field(default_factory=lambda: {
        "goal": "",           # What is the main objective?
        "progress": "",       # What has been accomplished so far?
        "current_approach": "",  # What strategy are we using?
        "key_findings": "",   # What important information have we discovered?
        "next_focus": ""      # What should be the next priority?
    })
    
    # Output
    response: Optional[str] = None
    respond_directly: bool = False
    verbose: bool = True
    trace: bool = False
    callback: Any = None
    notifications: List[Dict[str, Any]] = field(default_factory=list)
```

## Action Record Schema

**Purpose**: Rich debugging records. Tool-level compression fields are OBSOLETE.

```python
action_entry = {
    "iteration": int,
    "timestamp": str,          # ISO format
    "mode": str,              # "fast" | "deep"
    "thinking": str,          # LLM reasoning
    "planning": str,          # Deep mode planning
    "reflection": str,        # Deep mode reflection  
    "approach": str,          # Current strategy
    "tool_calls": [
        {
            "name": str,
            "args": dict,
            "result": str,        # Truncated to ~1000 chars
            "outcome": str,       # ToolOutcome enum value
            # NO per-tool compression fields - handled by situation_summary
        }
    ],
    # NO iteration-level compression fields - handled by situation_summary
}
```

## Context Assembly Methods

### Primary: Semantic Context
```python
def get_compressed_attempts(self, max_history: int = 3) -> List[str]:
    """Use situation_summary for intelligent context vs primitive truncation."""
    if any(v.strip() for v in self.situation_summary.values()):
        summary_parts = []
        for key, value in self.situation_summary.items():
            if value.strip():
                summary_parts.append(f"{key}: {value}")
        return ["; ".join(summary_parts)] if summary_parts else []
    
    # Fallback only if summary empty
    return compress_actions(self.actions[:-1][-max_history:])
```

### Clean Context Assembly
```python
def build_reasoning_context(self, mode: str, max_history: int = 3) -> str:
    """Clean context assembly using semantic compression."""
    if mode == "deep":
        # Deep: semantic summary + latest action details
        summary_context = self.format_actions_for_fast_mode(max_history)
        latest_context = self.format_latest_results_detailed()
        
        if summary_context == "No previous attempts":
            return latest_context if latest_context else "No context available"
        elif latest_context == "No tool results from current iteration":
            return summary_context
        else:
            return f"{summary_context}\n\nLATEST DETAILS:\n{latest_context}"
    else:
        # Fast: just semantic summary
        return self.format_actions_for_fast_mode(max_history)
```

## Reasoning Integration

### LLM Schema Extension
```python
# In unified reasoning prompt - LLM outputs:
{
  "summary_update": {
    "goal": "What is the main objective?",
    "progress": "What has been accomplished so far?", 
    "current_approach": "What strategy are we using?",
    "key_findings": "What important information have we discovered?",
    "next_focus": "What should be the next priority?"
  }
}
```

### State Update Logic
```python
# In reason.py - merge LLM updates into persistent summary:
if reasoning_response.summary_update:
    for key, value in reasoning_response.summary_update.items():
        if key in state.situation_summary and value.strip():
            state.situation_summary[key] = value
```

## Key Design Decisions

**1. Semantic vs Mechanical**
- LLM maintains living understanding vs string truncation
- 5 semantic fields vs 20+ complex compression fields
- Natural language synthesis vs brittle heuristics

**2. Single Source of Truth**
- `situation_summary` handles all context compression
- No redundant per-tool or per-iteration fields
- Clean separation: actions for debugging, summary for reasoning

**3. Graceful Degradation**
- Semantic summary takes priority when available
- Automatic fallback to basic compression if summary empty
- Handles edge cases (tool failures) transparently

**4. Zero Ceremony**
- LLM does the work, not complex code architecture
- Minimal state, maximum intelligence
- Beautiful simplicity

## Implementation Status

✅ **COMPLETE**: Semantic context summarization fully operational
❌ **OBSOLETE**: All tool-level and iteration-level compression fields
📋 **TODO**: Clean up obsolete fields from codebase

## Obsolete Patterns - DO NOT USE

```python
# OBSOLETE - handled by situation_summary
"synthesis": "",
"progress": "", 
"hypothesis": {"belief": "", "test": ""},
"insights": "",
"learning": "",
"relevance": "",
```

**Philosophy**: Elegant solutions supersede complex ones. Our semantic approach proves complexity was solving the wrong problem.