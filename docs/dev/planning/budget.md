# Budget & Cost Control Design

## Current State

- Fixed `max_iterations=10` regardless of query complexity
- No cost tracking or budget enforcement
- No query complexity classification
- Users can accidentally trigger expensive reasoning loops

## Proposed Solutions

### 1. Adaptive Iteration Limits

Replace fixed iteration limits with complexity-based scaling:

```python
def classify_query_complexity(query: str) -> str:
    """Classify query to set appropriate iteration budget."""
    if len(query) < 50 and "?" in query:
        return "simple"    # 2-3 iterations
    elif any(word in query.lower() for word in ["analyze", "research", "build", "debug"]):
        return "complex"   # 15+ iterations
    elif any(word in query.lower() for word in ["list", "show", "what", "when", "where"]):
        return "simple"    # 3-5 iterations
    return "medium"        # 8-10 iterations

agent = Agent("assistant", iteration_strategy="adaptive")
```

### 2. Cost Tracking & Budgets

#### Per-Query Limits
```python
agent = Agent("assistant",
    cost_limits={
        "max_tokens_per_query": 50000,  # Hard token stop
        "max_cost_per_query": 0.50,     # Dollar limit
        "query_timeout": 30             # Seconds
    }
)

# Or per-query override
result = agent.run("Analyze codebase", max_cost=0.25)
```

#### User Budgets
```python
agent.set_daily_budget(
    user_id="alice",
    tokens=100000,
    cost=5.00,
    queries=50
)

costs = agent.get_costs(user_id="alice", timeframe="today")
# Returns: {"tokens": 23450, "cost": 1.23, "queries": 12}
```

### 3. Smart Iteration Control

#### Progress Detection
Stop iterations early when no progress is made:

- Last 2 iterations show no new tool calls or insights → stop
- Error rate > 50% in last 3 iterations → stop  
- Same tool called 3x with identical args → stop
- No new information added to state → stop

#### Implementation Location
Add to `agent.py:168` reasoning loop:

```python
# Track progress indicators
progress_tracker = {
    "tool_calls": [],
    "errors": [],
    "state_changes": []
}

for iteration in range(iteration_budget):
    # ... existing reasoning ...
    
    # Check for progress
    if not self._detect_progress(progress_tracker, reasoning):
        emit("agent", state="early_stop", reason="no_progress")
        break
```

### 4. Provider Cost Optimization

Route queries to cost-appropriate providers:

```python
agent = Agent("assistant",
    provider_strategy={
        "simple": "groq",        # Fast + cheap for basic queries
        "complex": "anthropic",  # Capable for hard problems
        "embeddings": "nomic"    # Cost-effective embeddings
    }
)
```

#### Dynamic Provider Selection
```python
def select_provider(query_complexity: str, budget_remaining: float):
    if budget_remaining < 0.10:
        return "groq"  # Cheapest option
    elif query_complexity == "complex":
        return "anthropic"  # Best reasoning
    return "openai"  # Balanced default
```

### 5. Cost Calculation

#### Token Tracking
```python
def calculate_call_cost(self, provider: str, prompt_tokens: int, completion_tokens: int):
    """Calculate cost for LLM call."""
    rates = {
        "openai": {"input": 0.0015, "output": 0.002},  # per 1K tokens
        "anthropic": {"input": 0.003, "output": 0.015},
        "groq": {"input": 0.0001, "output": 0.0002}
    }
    
    rate = rates.get(provider, rates["openai"])
    return ((prompt_tokens * rate["input"]) + (completion_tokens * rate["output"])) / 1000
```

#### Budget Enforcement
```python
class BudgetExceeded(Exception):
    def __init__(self, spent: float, limit: float):
        super().__init__(f"Budget exceeded: ${spent:.3f} > ${limit:.3f}")
        self.spent = spent
        self.limit = limit

# In reasoning loop
if query_cost > budget.get("max_cost", 1.0):
    raise BudgetExceeded(query_cost, budget["max_cost"])
```

### 6. User Experience

#### Simple Budget API
```python
# Quick limits
result = agent.run("Complex query", max_cost=0.25, max_time=30)

# Detailed budgets  
agent.run("Query", budget={
    "max_cost": 0.50,
    "max_iterations": 15,
    "timeout": 60,
    "stop_on_error": True
})
```

#### Budget Status
```python
status = agent.budget_status(user_id="alice")
# {
#   "daily": {"used": 1.23, "limit": 5.00, "remaining": 3.77},
#   "query": {"tokens": 2340, "cost": 0.12}
# }
```

## Implementation Priority

1. **Adaptive iteration limits** - Immediate impact, low complexity
2. **Basic cost tracking** - Essential for budget features
3. **Per-query budget enforcement** - User safety
4. **Progress detection** - Prevent infinite loops
5. **User budgets** - Production feature
6. **Provider cost routing** - Optimization feature

## Files to Modify

- `src/cogency/agent.py` - Core budget logic
- `src/cogency/config/dataclasses.py` - Budget config classes  
- `src/cogency/providers/base.py` - Cost calculation
- `src/cogency/agents/reason.py` - Progress detection
- New: `src/cogency/budget/` - Budget management module

## Backward Compatibility

All budget features should be opt-in with sensible defaults:

```python
# Existing code continues to work
agent = Agent("assistant")  # No budget limits

# New opt-in features
agent = Agent("assistant", budgets=True)  # Default limits
agent = Agent("assistant", cost_limits={"max_cost": 1.0})  # Custom
```