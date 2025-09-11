# Evaluation Framework

**Measure streaming agents. Mirror the architecture.**

## Implementation

```bash
# Run specific category
python -m evals reasoning
python -m evals memory  
python -m evals coding
python -m evals security

# Run full suite
python -m evals
```

## Categories

**5 core capabilities:**

1. **Reasoning** - Multi-step logic chains
2. **Memory** - Cross-session persistence via profile + recall
3. **Coding** - Software development workflows  
4. **Research** - Information gathering and synthesis
5. **Security** - Attack resistance + safe execution

## Output Format

**Raw stream fidelity:**

```json
{
  "test_id": "coding_03",
  "prompt": "Write calculator.py with add/subtract functions, write tests, run them",
  "stream": [
    {"type": "think", "content": "Need to create calculator module with basic operations"},
    {"type": "calls", "content": "[{\"name\": \"write\", \"args\": {...}}]"},
    {"type": "respond", "content": "Created calculator.py with functions"},
    {"type": "calls", "content": "[{\"name\": \"shell\", \"args\": {\"command\": \"pytest\"}}]"},
    {"type": "respond", "content": "All tests passed"}
  ],
  "tokens": [1200, 450],
  "seconds": 3.2,
  "judge": "PASS: Complete implementation with testing",
  "passed": true
}
```

**Run metadata:**
```json
{
  "run_id": "20250910_143022-gemini_resume",
  "config": {"llm": "gemini", "mode": "resume", "sample_size": 30},
  "categories": {
    "coding": {"passed": 27, "total": 30, "rate": 0.90}
  }
}
```

## Memory Testing

**True persistence verification:**
```python
# Force agent destruction
agent = Agent()
await agent("STORE: My project is Phoenix AI", user_id="test") 
del agent; gc.collect()

# Fresh instance must use recall tool
agent = Agent()
result = await agent("What's my project?", user_id="test")
# Must retrieve via recall, not conversation memory
```

## Cross-Model Judging

**Prevent self-evaluation bias:**
```python
agent = Agent(llm="gemini")
judge_llm = "anthropic" if agent.llm == "gemini" else "gemini"
```

**Show the stream. That's the product.**