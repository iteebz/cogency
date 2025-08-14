# Cogency: Stateless Context-Driven Agent Framework

Context injection + LLM inference = complete reasoning engine.

After extensive research (342 commits), we discovered agents work better as functions.

## Quick Start

```python
from cogency import Agent

agent = Agent()
response = await agent("What are the benefits of async/await in Python?")
print(response)
```

## Architecture

```python
async def agent(query: str, user_id: str = "default") -> str:
    context = inject_context(query, user_id)
    return await llm.generate(f"{context}\n\nQuery: {query}")
```

## Design Principles

- **Zero writes** during reasoning
- **Pure functions** for context assembly  
- **Read-only** context sources
- **Graceful degradation** on failures

## Installation

```bash
pip install cogency
```

## Documentation

See `docs/blueprint.md` for technical specification.

*v2.0.0 represents a complete architectural rewrite based on empirical evidence that simpler approaches work better for LLM-based reasoning systems.*