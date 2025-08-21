# COGENCY

**Cogency is the `requests` library of AI agents.**

```python
from cogency import Agent

agent = Agent()
result = await agent("Debug this Python script")
```

**Simple things simple**: `Agent()` works out of the box
**Complex things possible**: Full configurability when needed

## ARCHITECTURE

AGENT -> CONTEXT -> INFRA
- **Agent**: Stateless orchestration
- **Context**: Assembles system, memory, conversation, working state  
- **Infra**: File system, LLM providers, storage

## RULES

1. **No global singletons with state**
2. **Agent constructor must be explicit** 
3. **Debug must be opt-in**

## USAGE

```python
agent = Agent()  # Production
agent = Agent(debug=True)  # Console logging
agent = Agent(debug="debug.log")  # File logging
agent = Agent(llm="gpt-4o")  # Specific model
```