# Cogency

**Streaming agents with stateless context assembly**

## Architecture

Cogency enables stateful agent execution through:

1. **Persist-then-rebuild**: Write every LLM output event to storage immediately, rebuild context from storage on each execution
2. **Delimiter protocol**: Explicit state signaling (`§think`, `§call`, `§execute`, `§respond`, `§end`)
3. **Stateless design**: Agent and context assembly are pure functions, all state externalized to storage

This eliminates stale state bugs, enables crash recovery, and provides concurrent safety by treating storage as single source of truth.

## Execution Modes

**Resume:** WebSocket session persists between tool calls
```python
agent = Agent(llm="openai", mode="resume")
# Maintains LLM session, injects tool results without context replay
# Constant token usage per turn
```

**Replay:** Fresh HTTP request per iteration
```python
agent = Agent(llm="openai", mode="replay")
# Rebuilds context from storage each iteration
# Context grows with conversation
# Universal LLM compatibility
```

**Auto:** Resume with fallback to Replay
```python
agent = Agent(llm="openai", mode="auto")  # Default
# Uses WebSocket when available, falls back to HTTP
```

## Token Efficiency

Resume mode maintains LLM session state, eliminating context replay on every tool call:

| Turns | Replay (context replay) | Resume (session state) | Efficiency |
|-------|------------------------|------------------------|------------|
| 8     | 31,200 tokens         | 6,000 tokens          | 5.2x       |
| 16    | 100,800 tokens        | 10,800 tokens         | 9.3x       |
| 32    | 355,200 tokens        | 20,400 tokens         | 17.4x      |

Mathematical proof: [docs/proof.md](docs/proof.md)

## Installation

```bash
pip install cogency
export OPENAI_API_KEY="your-key"
```

## Usage

```python
from cogency import Agent

agent = Agent(llm="openai")
async for event in agent("What files are in this directory?"):
    if event["type"] == "respond":
        print(event["content"])
```

### Event Streaming

**Semantic mode (default):** Complete thoughts
```python
async for event in agent("Debug this code", chunks=False):
    if event["type"] == "think":
        print(f"~ {event['content']}")
    elif event["type"] == "respond":
        print(f"> {event['content']}")
```

**Token mode:** Real-time streaming
```python
async for event in agent("Debug this code", chunks=True):
    if event["type"] == "respond":
        print(event["content"], end="", flush=True)
```

### Multi-turn Conversations

```python
# Stateless (default)
async for event in agent("What's in this directory?"):
    if event["type"] == "respond":
        print(event["content"])

# Stateful with profile learning
async for event in agent(
    "Continue our code review",
    conversation_id="review_session",
    user_id="developer"  # For profile learning and multi-tenancy
):
    if event["type"] == "respond":
        print(event["content"])
```

### Built-in Tools

- `read`, `write`, `edit`, `list`, `grep`
- `search`, `scrape`
- `recall`
- `shell`

### Custom Tools

```python
from cogency import Tool, ToolResult

class DatabaseTool(Tool):
    name = "query_db"
    description = "Execute SQL queries"
    
    async def execute(self, sql: str, user_id: str):
        # Your implementation
        return ToolResult(
            outcome="Query executed",
            content="Results..."
        )

agent = Agent(llm="openai", tools=[DatabaseTool()])
```

### Configuration

```python
agent = Agent(
    llm="openai",                    # or "gemini", "anthropic"
    mode="auto",                     # "resume", "replay", or "auto"
    storage=custom_storage,          # Custom Storage implementation
    identity="Custom agent identity",
    instructions="Additional context",
    tools=[CustomTool()],
    max_iterations=10,
    history_window=None,             # None = full history (default), int = sliding window
    profile=True,                    # Enable automatic user learning
    learn_every=5,                   # Profile update frequency
    debug=False
)
```

### Context Management

Cogency uses conversational message assembly for natural LLM interaction:

**Storage:** Events stored as typed records (clean content, no delimiters)
```python
{"type": "user", "content": "debug this"}
{"type": "think", "content": "checking logs"}
{"type": "call", "content": '{"name": "read", ...}'}
```

**Assembly:** Transforms to proper conversational structure
```python
[
  {"role": "system", "content": "PROTOCOL + TOOLS"},
  {"role": "user", "content": "debug this"},
  {"role": "assistant", "content": "§think: checking logs\n§call: {...}\n§execute"},
  {"role": "user", "content": "§result: ..."}
]
```

**Cost control with `history_window`:**
- `history_window=None` - Full conversation history (default)
- `history_window=20` - Last 20 messages (sliding window for cost control)
- Custom compaction: Query storage directly and implement app-level strategy

**Considerations:**
- Resume mode: Context sent once at connection, minimal impact
- Replay mode: Context grows with conversation, windowing recommended for long sessions
- Frontier models: Handle longer contexts better, can use `None`
- Weaker models: May benefit from smaller windows (e.g., 10-20 messages)

## Multi-Provider Support

```python
agent = Agent(llm="openai")     # GPT-4o Realtime API (WebSocket)
agent = Agent(llm="gemini")     # Gemini Live (WebSocket)
agent = Agent(llm="anthropic")  # Claude (HTTP only)
```





## Memory System

**Passive profile:** Automatic user preference learning
```python
agent = Agent(llm="openai", profile=True)
# Learns patterns from interactions, embedded in system prompt
```

**Active recall:** Cross-conversation search
```python
# Agent uses recall tool to query past interactions
§call: {"name": "recall", "args": {"query": "previous python debugging"}}
§execute
[SYSTEM: Found 3 previous debugging sessions...]
§respond: Based on your previous Python work...
```

## Streaming Protocol

Agents signal execution state explicitly:

```
§think: I need to examine the code structure first
§call: {"name": "read", "args": {"file": "main.py"}}
§execute
[SYSTEM: Found syntax error on line 15]
§respond: Fixed the missing semicolon. Code runs correctly now.
§end
```

Parser detects delimiters, accumulator handles tool execution, persister writes to storage.

See [docs/protocol.md](docs/protocol.md) for complete specification.

## Documentation

- [architecture.md](docs/architecture.md) - Core pipeline and design decisions
- [protocol.md](docs/protocol.md) - Delimiter protocol specification
- [proof.md](docs/proof.md) - Mathematical efficiency analysis

## License

Apache 2.0