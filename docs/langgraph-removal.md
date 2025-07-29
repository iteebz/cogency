# Why We Removed LangGraph: Technical Analysis

**TL;DR:** After 16 days of LangGraph integration, we removed it in favor of a simple execution loop. This document analyzes the decision and serves as institutional knowledge for future architectural choices.

## The Problem

LangGraph was causing infinite recursion issues in our agent loops (likely due to our state management patterns) and adding ceremony that didn't match our use case. This led us to question whether the abstraction was providing value.

## LangGraph Analysis: Where It Fits and Where It Doesn't

### 1. When Graph Abstraction Makes Sense (And When It Doesn't)

**LangGraph's Strength:** Complex workflows with parallel execution, human-in-the-loop approval, or dynamic routing benefit from graph representation.

**Our Use Case:** Linear agent workflows with simple conditional branching:
```
preprocess → reason → (tool execution loop) → respond
```

**LangGraph approach:**
```python
from langgraph.graph import StateGraph, END

graph = StateGraph(AgentState)
graph.add_node("agent", call_model)
graph.add_node("action", call_tool)
graph.add_conditional_edges("agent", should_continue)
graph.set_entry_point("agent")
compiled = graph.compile()
```

**Our simpler approach:**
```python
while state.iteration < state.depth:
    state = await reason(state, ...)
    if not state.tool_calls: break
    state = await act(state, ...)
```

**Assessment:** For our linear use case, the graph abstraction added ceremony without benefits. For complex workflows with multiple branches, it might be justified.

### 2. Error Handling Approaches

**LangGraph:** Generic retry mechanisms with configurable policies

**Our Approach:** Domain-specific resilience policies
```python
@robust.reason(retry=Retry.api())      # API-specific backoff for LLM calls
@robust.act(retry=Retry.db())          # DB-specific retry for tool execution
@robust.preprocess(timeout=10.0)       # Fast timeout for preprocessing
@robust.respond(timeout=15.0)          # Generous timeout for response generation
```

**Trade-off:** Our approach provides better handling for our specific domains (reasoning, tool execution, etc.) but is less general-purpose. LangGraph's generic approach works across more use cases but may not be optimal for any specific one.

### 3. State Management

**LangGraph:** Dict-based state: `state["some_key"] = value`

**Our Approach:** Structured, typed state with schema compliance
```python
state.add_action(
    mode="fast",
    thinking="User wants to search for information",
    planning="Use search tool then summarize",
    reflection="This approach should work",
    approach="direct_search",
    tool_calls=[{"name": "search", "args": {"query": "..."}}]
)
```

**Assessment:** Our structured approach provides better type safety and validation for our specific state schema. LangGraph's dict approach is more flexible for diverse use cases but offers less compile-time safety.

### 4. Recovery Strategies

**LangGraph:** Configurable retry and fallback mechanisms

**Our Recovery:** Context-aware strategies for specific error types
```python
if error.loop_detected:
    state["next_node"] = "respond"
    state["stop_reason"] = "loop_recovery"
    return Result.ok(state, recovery_action="force_respond")

if error.mode == "deep":
    state["react_mode"] = "fast"
    return Result.ok(state, recovery_action="fallback_to_fast")
```

**Trade-off:** Our approach handles our specific failure modes well but isn't generalizable. LangGraph's approach is more general but may not handle domain-specific cases optimally.

## What We Built Instead

### Simple Execution Loop
```python
async def run_agent(state: State, **kwargs) -> State:
    # Preprocessing
    state = await preprocess(state, **extract_kwargs(kwargs, preprocess))
    
    # Reasoning loop with iteration limits
    while state.iteration < state.depth:
        state = await reason(state, **extract_kwargs(kwargs, reason))
        if not state.tool_calls:
            break
        state = await act(state, **extract_kwargs(kwargs, act))
        state.iteration += 1
        if state.stop_reason:
            break
    
    # Final response
    state = await respond(state, **extract_kwargs(kwargs, respond))
    return state
```

**15 lines of clear execution for our use case.**

### Domain-Specific Exception Hierarchy
```python
class PreprocessError(CogencyError):
    def __init__(self, message: str, memory_failed: bool = False, **kwargs):
        
class ReasoningError(CogencyError):
    def __init__(self, message: str, mode: str = "unknown", loop_detected: bool = False, **kwargs):
        
class ActionError(CogencyError):
    def __init__(self, message: str, failed_tools: list = None, recoverable: bool = True, **kwargs):
```

**6 focused exception classes for our specific domains.**

### Context-Aware Recovery
```python
class Recovery:
    @staticmethod
    async def reasoning(error: ReasoningError, state: Any) -> Result:
        """Reasoning recovery - mode fallback and loop breaking."""
        if error.loop_detected:
            state["next_node"] = "respond"
            state["stop_reason"] = "loop_recovery"
            return Result.ok(state, recovery_action="force_respond")
        
        if error.mode == "deep":
            state["react_mode"] = "fast"
            return Result.ok(state, recovery_action="fallback_to_fast")
```

## Our Implementation Benefits

### 1. Simpler API for Linear Workflows
```python
# Our approach
agent = Agent("assistant", tools=tools)
result = agent.run("query")

# vs LangGraph setup
graph = StateGraph(AgentState)
# ... configuration ...
compiled = graph.compile()
result = compiled.invoke({"input": "query"})
```

### 2. Domain-Aware Defaults
Our `@robust` decorators understand the domain:
- **Reasoning:** Interruptible, API-style retry
- **Tool execution:** Interruptible, DB-style retry  
- **Preprocessing:** Non-interruptible, fast timeout
- **Response:** Non-interruptible, generous timeout

### 3. Structured Observability
Every action is logged with:
- Iteration number and timestamp
- Mode, thinking, planning, reflection
- Tool calls with outcomes
- Recovery actions taken

## Ecosystem Considerations

**Trade-off:** Removing LangGraph means losing integration with LangSmith and other LangChain ecosystem tools.

**Assessment:** For our current needs, the cleaner codebase outweighs ecosystem benefits. However, this decision may need revisiting if:
- We need complex workflow visualization
- Enterprise customers require LangSmith integration  
- We encounter use cases that benefit from graph-based orchestration

**Not Invented Here Risk:** We're potentially rebuilding functionality that exists in the ecosystem. This is justified for our core use case but should be monitored.

## Implementation Timeline

- **Day 1-5:** Initial LangGraph integration, learning the abstractions
- **Day 6-10:** Debugging infinite recursion issues (likely caused by our state management patterns conflicting with LangGraph's execution model)
- **Day 11-15:** Evaluating whether complexity was justified for our use case
- **Day 16:** Decision to remove LangGraph and implement simple execution loop

**Note:** The infinite recursion issues may have been resolvable with better understanding of LangGraph patterns, but the evaluation process revealed that our use case didn't require the abstraction.

## Engineering Lessons

### 1. Match Abstractions to Use Cases
Graph abstractions are powerful for complex workflows but can add unnecessary overhead for linear processes. Choose abstractions that match your problem domain.

### 2. Domain-Specific vs Generic Solutions
Our domain-specific error handling works well for our use case but may not generalize. Generic solutions like LangGraph handle more cases but may be suboptimal for specific domains.

### 3. Developer Experience vs Ecosystem Benefits
There's a real trade-off between clean, simple APIs and ecosystem integration. We chose simplicity, but this decision should be revisited as requirements evolve.

### 4. Technical Debt vs Feature Development
Building custom solutions creates maintenance burden but can provide better fit for specific needs. This requires ongoing evaluation.

## Future Considerations

**When This Decision Might Need Revisiting:**
- Complex workflows requiring parallel execution
- Human-in-the-loop approval processes
- Enterprise requirements for ecosystem integration
- Need for visual workflow debugging

**Our Competitive Advantages:**
- Simpler API for linear agent workflows
- Domain-specific error handling
- Structured state management
- Zero-ceremony execution

**Potential Disadvantages:**
- Limited to linear workflow patterns
- Missing ecosystem integrations
- Custom maintenance burden
- Reduced visual debugging capabilities

## Technical Results

**LangGraph Removal Status:** ✅ **Complete**

- Dependency removed from pyproject.toml
- All imports eliminated  
- Graph abstractions replaced with simple execution loop
- Infinite recursion issues resolved
- Reduced ceremony for our linear use case
- Maintained all functionality with simpler code

**Code Quality Improvements:**
- Clearer execution flow for our use case
- Better type safety with structured state
- Domain-specific error handling
- Reduced cognitive load for linear workflows

## Summary

For our specific use case (linear agent workflows with tool execution loops), removing LangGraph provided clear benefits in code simplicity and maintainability. This decision optimizes for our current needs while acknowledging that different use cases might benefit from LangGraph's graph-based approach.

---

*This document serves as institutional knowledge for future architectural decisions. It reflects our specific context and trade-offs, not universal principles.*