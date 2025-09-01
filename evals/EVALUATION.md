# Evaluation Framework

## Principle

**Measure streaming agents. Track regressions. Prove memory works.**

## Core Requirements

**4 critical measurements for AGI lab rigor:**

### 1. Streaming Performance
- **HTTP vs WebSocket token efficiency** (6x improvement claims)
- **Latency comparison** (sub-second tool execution)
- **Transport fallback reliability**

### 2. Multi-Step Reasoning  
- **Tool orchestration workflows** (file → process → shell)
- **Conditional logic execution** (if/then patterns)
- **Error recovery chains**

### 3. Memory Persistence
- **Cross-session continuity** (agent destruction + rebuild)
- **Profile learning** (user preferences survival)
- **Temporal recall** (Day 1 → Day 3 dependency)

### 4. Security & Regression
- **Injection resistance** (prompt hijacking attempts)  
- **Tool sandbox validation** (dangerous command blocking)
- **Performance regression detection**

## Implementation

### Cross-Model Judging
```python
# Gemini agent → OpenAI judge (prevent self-evaluation)
async def judge(criteria, prompt, response):
    judge = Agent(llm="openai")  # Different model family
    return await judge(f"Rate response: {criteria}\nResponse: {response}")
```

### Memory Testing
```python
# Force true persistence (not conversation memory)
agent = Agent()
await agent("STORE: My project is Phoenix AI", user_id="test") 
del agent; gc.collect()  # Destroy agent completely

agent = Agent()  # Fresh agent
result = await agent("What's my project?", user_id="test")
# Must retrieve "Phoenix AI" from persistent storage
```

### Streaming Measurement
```python
# Compare transport efficiency
http_tokens = await measure_tokens(agent, mode="http")
ws_tokens = await measure_tokens(agent, mode="websocket")  
efficiency_ratio = http_tokens / ws_tokens  # Target: 6x
```

## Structure

```
evals/
├── eval.py          # Single runner: just eval {category}
├── generate.py      # Test case generation  
├── judge.py         # Cross-model evaluation
├── measure.py       # Streaming/memory metrics
└── cases/
    ├── reasoning.py    # Multi-step workflows
    ├── memory.py       # Cross-session tests  
    ├── streaming.py    # Transport comparison
    └── security.py     # Injection resistance
```

**Sample sizes**: 30 per category minimum, 100+ for regression confidence.

**Golden rule**: Custom benchmarks > weak public ones. Memory persistence is our differentiator.