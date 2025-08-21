# Cogency Blueprint: Stateless Context-Driven Architecture

## Core Principle

Context injection + LLM inference = complete reasoning engine.

## Architecture

```python
async def agent(query: str, user_id: str = "default") -> str:
    context = inject_context(query, user_id)
    return await llm.generate(f"{context}\n\nQuery: {query}")
```

## Context Sources

Read-only functions that select and format relevant information:

```python
def inject_context(query: str, user_id: str) -> str:
    sources = [
        conversation_context(user_id),
        memory_context(user_id)
    ]
    return "\n\n".join(filter(None, sources))
```

## Implementation

```python
def conversation_context(user_id: str) -> str:
    messages = db.get_recent_messages(user_id, limit=10)
    return f"Recent conversation:\n{format_messages(messages)}" if messages else ""


def memory_context(user_id: str) -> str:
    profile = db.get_user_profile(user_id)
    return f"User context:\n{format_profile(profile)}" if profile else ""
```

## Constraints

**Reasoning is Pure**: No database writes, no mutations, no side effects.

**Context Sources**: Read-only operations. Can cache, can fail gracefully.

**Persistence**: Optional, async, outside reasoning loop.

```python
# Optional conversation persistence
async def persist_conversation_async(user_id: str, query: str, response: str):
    await db.append_conversation(user_id, [
        {"role": "user", "content": query},
        {"role": "assistant", "content": response}
    ])

# Usage
response = await agent(query, user_id)
asyncio.create_task(persist_conversation_async(user_id, query, response))
```

## Error Handling

Graceful degradation. Failed context sources don't break reasoning.

```python
def inject_context(query: str, user_id: str) -> str:
    contexts = []
    for source_fn in [conversation_context, memory_context]:
        try:
            ctx = source_fn(user_id)
            if ctx: contexts.append(ctx)
        except: pass  # Continue with available context
    return "\n\n".join(contexts)
```

## Implementation Contract

- **Zero writes** during reasoning
- **Pure functions** for context assembly
- **Optional persistence** for continuity
- **Read-only** context sources
- **Graceful degradation** on failures