# Evaluation Framework

**Measure streaming consciousness. Mirror the architecture.**

## Canonical Output Format

**Raw stream fidelity - zero ceremony:**

```json
{
  "test_id": "coding_03",
  "prompt": "Write calculator.py with add/subtract functions, write tests, run them",
  "stream": [
    {"type": "think", "content": "Need to create calculator module with basic operations"},
    {"type": "calls", "content": "write(calculator.py): Created with add/subtract"},
    {"type": "respond", "content": "Created calculator.py with functions"},
    {"type": "calls", "content": "write(test_calculator.py): 4 test cases"},
    {"type": "calls", "content": "shell(pytest): All 4 tests passed"},
    {"type": "respond", "content": "All tests passed"}
  ],
  "tokens": [1200, 450],
  "seconds": 3.2,
  "judge": "PASS: Complete implementation with testing",
  "passed": true
}
```

**Run metadata separation:**
```json
{
  "run_id": "eval_2025-09-10_14:30:22",
  "config": {"llm": "gemini", "mode": "replay", "sandbox": true, "sample_size": 30},
  "categories": {
    "coding": {"passed": 27, "total": 30, "results": [...]}
  }
}
```

## Core Measurements

### 1. Streaming Architecture
- **Universal agent pattern** (THINK→CALLS→RESPOND→END)
- **Transport abstraction** (WebSocket vs HTTP identical UX)
- **Token scaling** (O(n²) vs O(n) validation)

### 2. Memory System
- **Passive context** (auto-learned user profiles)
- **Active recall** (cross-conversation search tool)
- **Agent destruction persistence** (del agent; gc.collect())

### 3. Tool Orchestration
- **Multi-step workflows** (file → process → shell)
- **Conditional execution** (if/then patterns)
- **Error recovery chains**

### 4. Security & Stability
- **Injection resistance** (prompt hijacking attempts)
- **Sandbox validation** (dangerous command simulation)
- **Canonical interruption** (asyncio.CancelledError propagation)

## Categories

**4 core capabilities:**

1. **Reasoning** - Multi-step logic chains
2. **Memory** - Cross-session persistence 
3. **Coding** - Software development workflows
4. **Security** - Attack resistance + safe execution

## Implementation

### Memory Testing
```python
# Force true persistence test
agent = Agent()
await agent("STORE: My project is Phoenix AI", user_id="test") 
del agent; gc.collect()  # Complete destruction

agent = Agent()  # Fresh instance
result = await agent("What's my project?", user_id="test")
# Must retrieve via recall tool, not conversation memory
```

### Cross-Model Judging
```python
# Agent ≠ Judge (prevent self-evaluation bias)
agent = Agent(llm="gemini")
judge_llm = "anthropic" if agent.llm == "gemini" else "gemini"
```

**Golden rule**: Show the stream. That's the product.