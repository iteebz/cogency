# Adaptive Reasoning Architecture
*The first agent system to achieve cognitive parsimony*

## The Breakthrough

This architecture enables agents to **dynamically modulate cognitive complexity**—switching in real time between fast, lightweight ReAct and deep, reflective UltraThink based on task difficulty, without requiring new nodes or hardcoded heuristics.

**This solves the fundamental problem that's plagued agent systems since inception**: cognitive resource allocation. Instead of forcing every task through the same cognitive process, agents now adaptively adjust their thinking based on what the task actually requires.

### Revolutionary Approach

- **Runtime complexity discovery** instead of upfront classification
- **Zero extra LLM calls** - switching happens within existing reasoning
- **Self-correcting** - eliminates classification errors through adaptation
- **LLM-governed escalation/de-escalation** with full semantic understanding

## Mental Model

**Fast React = Pure ReAct**  
`Thought → Action → Observation` (direct execution)

**Deep React = ReAct + UltraThink**  
`REFLECTION → PLANNING → EXECUTION` (sophisticated reasoning)

## Core Innovation: Bidirectional Mode Switching

```
    ┌─────────────┐    Task needs deeper     ┌──────────────┐
    │ Fast React  │ ────── analysis ──────► │ Deep React   │
    │ Pure ReAct  │                          │ + UltraThink │
    │             │ ◄──── simpler than ──────│              │
    └─────────────┘       expected          └──────────────┘
```

**Fast → Deep**: Escalate when sophisticated analysis needed  
**Deep → Fast**: Optimize when task simpler than expected  
**Self-Correcting**: Runtime adaptation eliminates wrong classifications

## Architecture

### Clean Modular Design
```
reasoning/
├── adaptation.py     # Bidirectional mode switching 
├── reflection.py     # UltraThink phases (REFLECTION→PLANNING→EXECUTION)
├── planning.py       # Multi-step strategy creation
├── relevance.py      # LLM-based memory scoring
└── prompts.py       # Centralized prompt management
```

### Adaptive Features

| Feature | Fast React | Deep React |
|---------|------------|------------|
| **Reasoning** | Direct ReAct execution | UltraThink reflection phases |
| **Memory** | FIFO (3 recent) | LLM semantic scoring (10 relevant) |
| **Loop Detection** | Lightweight (2 actions) | Sophisticated patterns (3+ actions) |
| **Cost** | Minimal tokens | Rich context + reflection |

## Key Components

### 1. Bidirectional Adaptation
- **Semantic switching**: LLM decides complexity needs during execution  
- **Context preservation**: Full cognitive state maintained across switches
- **Graceful boundaries**: No switching too early (< iteration 1) or late (≥ iteration 4)

### 2. UltraThink Integration (Deep Mode)
- **🤔 REFLECTION**: "What have I learned? What's working/not working?"
- **📋 PLANNING**: "Based on analysis, here's my multi-step strategy"  
- **🎯 EXECUTION**: "Now I'll take this specific action"

### 3. LLM-Based Relevance Scoring  
- **Zero heuristics**: Pure semantic understanding for memory management
- **Adaptive retention**: High-relevance items persist longer
- **Graceful fallback**: FIFO when LLM scoring fails

### 4. Enhanced Loop Detection
- **Mode-aware**: Different thresholds for Fast (lightweight) vs Deep (sophisticated)
- **Pattern recognition**: Detects repeated unsuccessful strategies
- **Smart intervention**: Prevents cognitive loops before they waste resources

## Revolutionary Benefits

**Cognitive Parsimony**: Using exactly as much reasoning as needed, no more, no less.

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

*The world's first agent system with genuine cognitive adaptivity - using intelligence to govern intelligence.*