# PRINCIPLES

**Cogency v2.0.0 architectural decisions.**

## Context is all you need

**Stateless agents with pure function context assembly.**

```python
# Agent: single interface
await Agent()(query, user_id) -> str

# Context: structured messages
context(query, user_id) -> list[dict]
```

## Domain hierarchy

**Dependencies flow down:**

```
cogency.*           # Public API
    ↓
agent.py            # Stateless execution
    ↓ 
context.*           # Pure function assembly
    ↓
storage.py          # JSON persistence
    ↓
providers.*         # LLM integration
```

## Context sources

```python
system() -> str                           # Base prompt
conversation(user_id) -> list[dict]       # Message history  
knowledge(query, user_id) -> str          # Document search
memory(user_id) -> str                    # User profile
working(tools) -> str                     # Tool results
```

## Error handling

**All context functions fault-tolerant:**

```python
try: return valid_result()
except: return fallback()  # "", [], etc.
```

**Never break agent execution.**

## Storage

- **Location**: `~/.cogency/`
- **Format**: JSON files  
- **Pattern**: Fire-and-forget persistence

## Violations

- Complex state during reasoning
- Database writes during execution
- String concatenation for conversation
- Context assembly throwing exceptions

---

**See `/docs/standards.md` for implementation requirements.**