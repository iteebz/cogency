# Adaptive Reasoning

**Thinks fast or deep as needed.**

Agents dynamically switch between Fast React (direct execution) and Deep React (reflection + planning) based on task complexity discovered at runtime.

## The Innovation

- **Runtime discovery** - Agents discover task complexity during execution
- **Zero extra calls** - Mode switching happens within existing reasoning  
- **Self-correcting** - Eliminates upfront classification errors
- **Bidirectional** - Can escalate to Deep or optimize to Fast

## Two Modes

**Fast React**: Direct ReAct execution for simple tasks  
**Deep React**: Reflection + planning phases for complex analysis

## Core Innovation: Seamless Mode Switching

```
    ┌─────────────┐    Task needs deeper     ┌──────────────┐
    │ Fast React  │ ────── analysis ──────► │ Deep React   │
    │ Pure ReAct  │                          │ + UltraThink │
    │             │ ◄──── simpler than ──────│              │
    └─────────────┘       expected          └──────────────┘
```

**Fast → Deep**: Escalate when sophisticated analysis needed  
**Deep → Fast**: Optimize when task simpler than expected  
**Self-Correcting**: Runtime adaptation eliminates upfront classification errors

## Architecture

### Clean Modular Design

```
reasoning/
├── fast.py           # Fast React mode prompting & parsing
├── deep.py           # Deep React mode with structured thinking
└── adaptive/         # Adaptive reasoning subsystem
    ├── cognition.py  # Three-level cognitive state tracking
    ├── switching.py  # Bidirectional mode switching logic
    ├── loop.py       # Mode-aware loop detection
    ├── assessment.py # Tool execution quality assessment
    └── relevance.py  # LLM-based memory scoring
```

### Adaptive Features

| Feature            | Fast React              | Deep React                          |
| ------------------ | ----------------------- | ----------------------------------- |
| **Reasoning**      | Flat `thinking` field   | Structured `thinking` object (reflection→planning→decision) |
| **Memory**         | FIFO (3 recent)         | LLM semantic scoring (10 relevant)  |
| **Loop Detection** | Lightweight (2 actions) | Sophisticated patterns (3+ actions) |
| **Cost**           | Minimal tokens          | Rich context + reflection           |

## Key Components

### 1. Bidirectional Adaptation

- **Semantic switching**: LLM decides complexity needs during execution
- **Context preservation**: Full cognitive state maintained across switches
- **Graceful boundaries**: No switching too early (< iteration 1) or late (≥ iteration 4)

### 2. Three-Level Cognitive Tracking

**Hierarchical State Management:**
- **approach_history**: High-level strategic approaches attempted
- **decision_history**: Specific decisions made within approaches  
- **action_fingerprints**: Unique signatures of tool call patterns

### 3. Deep Mode Structured Thinking

**UltraThink Integration:**
```json
{
  "thinking": {
    "reflection": "What I've learned? What's working/not working?",
    "planning": "Based on analysis, here's my multi-step strategy", 
    "decision": "This is what I've decided and why"
  }
}
```

- **REFLECTION**: What happened (past analysis)
- **PLANNING**: What to do (future strategy)
- **DECISION**: What I've decided and why (present choice)

### 4. LLM-Based Relevance Scoring

- **Zero heuristics**: Pure semantic understanding for memory management
- **Adaptive retention**: High-relevance items persist longer
- **Graceful fallback**: FIFO when LLM scoring fails

### 5. Enhanced Loop Detection

- **Mode-aware**: Different thresholds for Fast (lightweight) vs Deep (sophisticated)
- **Pattern recognition**: Detects repeated unsuccessful strategies
- **Smart intervention**: Prevents cognitive loops before they waste resources

## Revolutionary Benefits

**Cognitive Parsimony**: Thinks as hard as needed, no more, no less.

- **Runtime Intelligence**: Discovers actual task complexity during execution
- **Resource Efficiency**: Simple tasks stay fast, complex tasks get proper depth
- **Self-Correction**: Eliminates upfront classification errors through adaptation
- **Maintained Simplicity**: Enhances ReAct without breaking the core paradigm

## Philosophy

**This isn't just state-of-the-art—it's a new standard for adaptive, efficient, and composable AI reasoning.**

- **Enhance, don't replace**: ReAct paradigm preserved and enhanced
- **Zero ceremony**: No extra nodes, calls, or architectural complexity
- **Modular elegance**: Clean separation enables easy testing and extension
- **Intelligent adaptation**: LLM-governed cognitive resource allocation

---

## Future Extensions

### Advanced Planning Capabilities

Multi-step planning with dependency tracking, resource allocation, and plan revision based on intermediate results.

### Hypothesis-Driven Search Patterns

Systematic hypothesis generation and testing for complex research queries.

### Structured Scratchpad Framework

The Goal/Plan/Current Step/Findings/Reflection structure.

### Multi-Source Corroboration Requirement (Search)

Explicit instruction to find multiple sources for critical data points.

---

_The world's first agent system with runtime cognitive adaptation - intelligence that governs itself._
