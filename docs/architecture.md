# architecture

## react reasoning loop

Cogency agents use **ReAct** (Reason-Act-Observe) for multi-step reasoning:

```
🧠 REASON → ⚡ ACT → 👀 OBSERVE
```

### phases

1. **reason**: determine strategy and tool selection
2. **act**: execute tools with prepared inputs  
3. **observe**: evaluate outputs and decide next steps

Loop continues until task is complete, then agent responds.

### streaming execution

Each phase streams live updates for transparency:

```python
async for chunk in agent.stream("complex query"):
    print(chunk, end="", flush=True)
# Shows: 🧠 REASON → ⚡ ACT → 👀 OBSERVE → 💬 RESPOND
```