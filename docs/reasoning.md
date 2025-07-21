# Enhanced Cognitive Reasoning Architecture

## Scope & Implementation Status

### ✅ IN SCOPE (Core Implementation - COMPLETED)
- Enhanced reason_node with structured reflection prompts
- State tracking for strategy history, failed attempts, tool result quality  
- Smart context management - summarize failures, track patterns
- Loop detection - redundancy flagging, iteration caps, forced strategy shifts
- Graceful degradation - fallback to simple reasoning if structured fails

### 🔄 EXTENDED SCOPE (Phase 2 - Future)
- Task-specific activation - enhanced reasoning only for complex queries
- Adaptive summarization - rolling windows, capped memory
- Hypothesis-driven search patterns
- Multi-source corroboration logic

### 🚫 OUT OF SCOPE
- Separate reflection node (too costly)
- Major architecture changes to 4-node flow
- New tools or external dependencies
- Breaking changes to existing Agent API

## Key Superseded Concepts
- **Scratchpad**: Replaced by structured `cognitive_state` with precise tracking
- **Gemini suggestions**: Influenced structured reasoning framework
- **Hypothesis-driven**: Deferred to Phase 2, focus on adaptive strategy first

## Overview
This document outlines the enhanced reasoning capabilities for Cogency agents, designed to prevent "plan fixation" and improve adaptive problem-solving across all use cases.

## Core Philosophy
- **Enhance ReAct, don't replace it** - Keep existing 4-node flow intact
- **Single LLM call per cycle** - No additional reflection nodes
- **Structured reasoning over raw prompts** - Organized cognitive scaffolding
- **Smart context management** - Summarize failures, track patterns

## Architecture

### Enhanced Reason Node
The `reason_node` is enhanced with structured reflection capabilities:

```python
REASON_PROMPT = """
COGNITIVE CONTEXT:
Previous attempts: {previous_attempts}
Current strategy: {current_strategy}
Tool results quality: {last_tool_quality}
Iteration: {current_iteration}/{max_iterations}

REASONING FRAMEWORK:
Goal: {extracted_goal}
Last Step: {last_action_summary}
Finding: {last_result_assessment}
Reflection: {strategy_assessment}
New Step: {proposed_next_action}

Now analyze and decide next action...
"""
```

### State Enhancements
New state tracking for cognitive continuity:

```python
state["strategy_history"] = ["search_direct", "search_broader", "search_technical"]
state["failed_attempts"] = [
    {"tool": "search", "query": "X", "result_quality": "poor", "reason": "too_generic"},
    {"tool": "search", "query": "Y", "result_quality": "partial", "reason": "missing_context"}
]
state["context_summary"] = "Previous searches for plan fixation failed with generic results"
state["current_strategy"] = "hypothesis_driven_search"
state["goal_analysis"] = "Find technical details about AI agent loop prevention"
```

## Key Components

### 1. Loop Detection & Prevention
- **Redundancy flagging** - Track similar queries/actions
- **Iteration caps** - Hard limits on reasoning cycles
- **Strategy shift triggers** - Force new approaches when stuck

### 2. Smart Context Management
- **Failure summarization** - Keep insights, discard noise
- **Pattern recognition** - Identify recurring failure modes
- **Rolling windows** - Maintain bounded memory

### 3. Structured Reflection
- **Goal tracking** - Maintain objective clarity
- **Strategy assessment** - Evaluate current approach effectiveness
- **Quality evaluation** - Assess tool result usefulness

### 4. Graceful Degradation
- **Fallback mechanisms** - Revert to simple reasoning if structured fails
- **Progressive complexity** - Start simple, add structure as needed
- **Error recovery** - Handle malformed reasoning gracefully

## Implementation Benefits

### General Cognition Enhancement
- **Adaptive problem-solving** across all task types
- **Reduced infinite loops** in complex scenarios
- **Better strategy selection** based on past experience
- **Improved context synthesis** from multiple sources

### Specific Research Improvements
- **Dynamic search strategy** adaptation
- **Multi-perspective analysis** capability
- **Source quality assessment** and filtering
- **Conflict resolution** between information sources

## Migration Path

### Phase 1: Core Implementation
1. Enhanced `reason_node` prompting
2. Basic state tracking for strategies/failures
3. Simple loop detection and caps
4. Graceful degradation mechanisms

### Phase 2: Advanced Features
1. Task-specific activation patterns
2. Adaptive summarization algorithms
3. Hypothesis-driven search frameworks
4. Multi-source corroboration logic

## Success Metrics
- **Reduced loop incidents** in research tasks
- **Improved task completion rates** for complex queries
- **Better strategy adaptation** when initial approaches fail
- **Maintained performance** for simple tasks (no regression)

## Technical Notes
- **Single LLM call overhead** - No additional API costs
- **Backward compatibility** - Existing agent APIs unchanged
- **Modular design** - Components can be enabled/disabled
- **Language model agnostic** - Works with any capable LLM

---

*This architecture provides general cognitive enhancement while solving specific research agent fixation issues.*