# Learning & Memory Systems

Cogency provides two independent memory systems: **Profile Learning** (passive user preference learning) and **Recall Tool** (active agent memory search). History window is a cost control knob.

## Profile Learning

Passive learning of user preferences triggered every N messages.

**Enable it:**
```python
agent = Agent(llm="openai", profile=True, user_id="alice")

async for event in agent("Debug this", user_id="alice"):
    if event["type"] == "respond":
        print(event["content"])
```

**How it works:**
1. Every 5 user messages (or when profile > 2000 chars), LLM analyzes conversation
2. Generates/updates JSON profile with user patterns
3. Profile automatically prepended to system prompt on next turn
4. Fire-and-forget async—doesn't block conversation

**Profile format** (LLM decides structure):
```json
{
  "who": "senior backend engineer",
  "style": "direct, technical",
  "focus": "distributed systems",
  "interests": "Rust, Go, performance",
  "misc": "timezone UTC+1",
  "_meta": {"last_learned_at": 1699564800.0}
}
```

**When to enable:**
- Multi-turn sessions with personalization value
- Long interactions (learns over time)
- Cost of learning < value of personalization

**Privacy:** Human-readable JSON, fully transparent, deletable.

## Recall Tool

Active agent-initiated memory search across conversation history.

**How it works:**
- Agent calls `recall(query="python debugging")` when needed
- SQLite fuzzy search (no embeddings—simpler, transparent)
- Returns top 3 cross-conversation matches
- Excludes recent messages to avoid repeating current context

**Agent behavior:**
When solving similar problems, agent calls recall tool to find past interactions:
```
recall(query="python multiprocessing debugging")
→ Returns: [3h ago debugging subprocess locks, 1d ago GIL problem]
Agent responds: "Based on your previous multiprocessing work..."
```

**Enable:**
```python
agent = Agent(llm="openai", tools=tools())  # Recall included by default
```

**Why SQLite not embeddings:**
- No vector DB infrastructure
- Transparent & queryable (users can inspect)
- No embedding latency/cost
- Keyword search finds candidate messages, LLM evaluates relevance
- 80% semantic value at 20% implementation complexity

## History Window

Cost control for Replay mode. Applies sliding window to conversation history.

**Without window** (default):
```
Turn 1: context=[msg1]
Turn 2: context=[msg1, msg2]
Turn 100: context=[msg1...msg100]
```

**With window=20:**
```
Turn 100: context=[msg81...msg100]  (sliding window, constant size)
```

**Cost impact (Replay mode):**
| Session | No Window | Window=20 | Savings |
|---|---|---|---|
| 50 turns | ~15k tokens | ~6k tokens | 60% |
| 100 turns | ~50k tokens | ~6k tokens | 88% |
| 200 turns | ~200k tokens | ~6k tokens | 97% |

**When to use:**
- Long sessions (100+ turns) in Replay mode → window=20
- Cost-sensitive → window=10-15
- Resume mode or short sessions → window=None (full history is cheap)

## Combining All Three

| System | Type | Trigger | Purpose |
|---|---|---|---|
| Profile | Passive | Every N messages | Ambient user preferences |
| Recall | Active | Agent decides | Targeted past interaction search |
| History window | Cost control | Always applied | Limit context size in Replay mode |

**Stateful assistant with personalization:**
```python
agent = Agent(
    llm="openai",
    mode="resume",       # Efficient streaming
    profile=True,        # Learn user style
    user_id="alice",
    history_window=None, # Full history (cheap in resume)
    tools=tools(),       # Includes recall
)

# Profile learns in background, agent can call recall()
```

**Cost-optimized Replay:**
```python
agent = Agent(
    llm="openai",
    mode="replay",
    profile=False,
    history_window=10,   # Keep last 10 messages
)
```

**Stateless (no memory):**
```python
agent = Agent(llm="openai", mode="auto")
# No conversation_id, no user_id → ephemeral
```

## Architecture

**Profile vs Recall:**
- Profile is passive background learning of broad preferences
- Recall is active agent-initiated search for specific past interactions
- Combine for personalization (profile) + targeted memory (recall)

**Why JSON profiles not embeddings:**
- Human-readable (not opaque vectors)
- Queryable & editable (introspectable)
- No model drift over time
- Transparent to users

Cost: Requires LLM re-analysis each cycle. Worth it.

## API

```python
from cogency.context import profile

# Check if learning triggered
should_learn = await profile.should_learn(user_id, storage=storage)

# Get current profile
current = await profile.get(user_id, storage=storage)

# Format for system prompt (called automatically)
formatted = await profile.format(user_id, storage=storage)

# Manual trigger learning (automatic, but can force)
updated = await profile.learn_async(user_id, storage=storage, llm=llm)
```

## Debugging

Enable debug logging:
```python
agent = Agent(llm="openai", debug=True)  # Logs to .cogency/debug/
```

Look for profile learning in logs:
```
LEARNING: 5 new messages for user=alice
```

Inspect stored profile:
```python
from cogency.context import profile
import json

current = await profile.get("alice", storage=storage)
print(json.dumps(current, indent=2))
```
