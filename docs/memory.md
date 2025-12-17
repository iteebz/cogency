# Memory

Three independent systems: **Profile** (passive learning), **Recall** (active search), **History Window** (cost control).

## Profile Learning

Passive user preference learning triggered every N messages.

```python
agent = Agent(llm="openai", profile=True)
async for event in agent("query", user_id="alice"):
    ...
```

**How it works:**
1. Every 5 user messages, LLM analyzes conversation
2. Generates/updates JSON profile with user patterns
3. Profile prepended to system prompt on next turn
4. Fire-and-forget async—doesn't block conversation

**Profile format:**
```json
{
  "who": "senior backend engineer",
  "style": "direct, technical",
  "focus": "distributed systems",
  "interests": "Rust, Go, performance",
  "misc": "likes cats, morning person",
  "_meta": {"last_learned_at": 1699564800.0, "messages_processed": 10}
}
```

Human-readable, transparent, deletable.

## Recall Tool

Active agent-initiated search across conversation history.

```python
agent = Agent(llm="openai", tools=tools())  # Recall included by default
```

**How it works:**
- Agent calls `recall(query="python debugging")` when needed
- SQLite fuzzy search (no embeddings)
- Returns top 3 cross-conversation matches
- Excludes current conversation

**Why SQLite not embeddings:**
- No vector DB infrastructure
- Transparent & queryable
- No embedding latency/cost
- 80% semantic value at 20% complexity

## History Window

Cost control for Replay mode. Sliding window on conversation history.

```python
agent = Agent(llm="openai", mode="replay", history_window=20)
```

| Session | No Window | Window=20 | Savings |
|---------|-----------|-----------|---------|
| 50 turns | ~15k tokens | ~6k tokens | 60% |
| 100 turns | ~50k tokens | ~6k tokens | 88% |

**When to use:**
- Long sessions in Replay mode → `history_window=20`
- Resume mode → `history_window=None` (full history is cheap)

## Combining Systems

| System | Type | Trigger | Purpose |
|--------|------|---------|---------|
| Profile | Passive | Every N messages | Ambient preferences |
| Recall | Active | Agent decides | Past interaction search |
| History Window | Cost control | Always | Limit context size |

```python
# Full-featured
agent = Agent(
    llm="openai",
    mode="resume",
    profile=True,
    tools=tools(),
)
# user_id passed per-call: agent("query", user_id="alice")

# Cost-optimized
agent = Agent(
    llm="openai",
    mode="replay",
    history_window=10,
)

# Stateless
agent = Agent(llm="openai")  # No user_id → ephemeral
```

## API

```python
from cogency.context import profile

current = await profile.get(user_id, storage=storage)
formatted = await profile.format(user_id, storage=storage)
learned = await profile.learn_async(user_id, storage=storage, llm=llm)
```
