# Cogency: AI Reasoning Framework

## Mission
Multistep AI reasoning framework with **NO BULLSHIT** philosophy. Zero ceremony, beautiful DX, plug-and-play everything.

## Core Philosophy: NO BULLSHIT DOCTRINE

### 🔥 WORLD-CLASS CODE CRITERIA
- **DRY + SOLID**: No duplicate patterns, readable names over comments
- **Decoupled + Extensible**: Loose coupling, obvious extension points
- **Pragmatic + Modular**: Solve real problems, small focused files
- **Auto-magical**: Smart defaults, zero ceremony
- **Beautiful**: Decorators, functional composition, intuitive APIs
- **Zero Line Philosophy**: Every line must justify itself

### 🚩 BULLSHIT (violate world-class criteria)
- DRY violations, tight coupling, over-engineering
- Giant files (200+ lines), wheel reinvention
- Import ceremony, ceremonial naming
- Abstract base classes adding complexity not hiding it

## Architecture

### PRARR Workflow
```
PLAN → REASON → ACT → REFLECT → RESPOND
```
- **PLAN**: Break down user query into actionable steps
- **REASON**: Analyze context and determine approach  
- **ACT**: Execute tools and gather information
- **REFLECT**: Evaluate results and determine next steps
- **RESPOND**: Generate final response to user

### Core Components

#### Agent (6-line magical DX)
```python
from cogency import Agent

agent = Agent("assistant")
result = await agent.run("Hello world")
```

#### Flow (formerly CognitiveWorkflow)
- Abstracts LangGraph complexity
- Handles PRARR workflow orchestration
- Streaming traces by default

#### Smart Memory
- **Auto-storage**: Detects personal info without ceremony
- **Smart recall**: Word-based matching for natural queries
- **Plug-and-play**: FSMemory, Pinecone, ChromaDB support

```python
# Auto-stores "I have ADHD" without explicit memorize command
agent.run("I have ADHD and work as a software engineer")

# Later naturally recalls
agent.run("What do you know about my work situation?")
```

#### Tools
- Auto-discovery via registry
- Clean PRARR traces (no JSON dumps)
- Extensible tool system

## Current State
- ✅ 20 unit tests passing
- ✅ Smart memory with auto-storage heuristics
- ✅ Clean PRARR traces for all tools
- ✅ Plug-and-play memory backends
- ✅ Beautiful streaming DX

## Key Files
- `src/cogency/agent.py`: 6-line magical Agent DX
- `src/cogency/workflow.py`: Flow (PRARR orchestration)
- `src/cogency/memory/filesystem.py`: Smart memory with auto-storage
- `src/cogency/tools/`: Auto-discovered tool registry
- `examples/`: Clean integration examples

## Design Principles
1. **Magical DX**: Should just work with minimal setup
2. **No ceremony**: Auto-detection over configuration
3. **Extensible**: Plugin architecture for everything
4. **Beautiful traces**: Live streaming PRARR workflow
5. **Smart defaults**: Opinionated but flexible
6. **Plug-and-play**: Swap backends without code changes

## Anti-patterns Eliminated
- ❌ Ceremony memory ("remember this" commands)
- ❌ Complex imports (single magical import)
- ❌ Hardcoded backends (pluggable everything)
- ❌ Messy traces (clean summaries)
- ❌ Manual tool registration (auto-discovery)

**Mantra: If it's not jaw-dropping beautiful, it's BULLSHIT.**