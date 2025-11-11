# Cogency

Streaming agents with stateless context assembly.

## Core Design

1. **Persist-then-rebuild**: Write events to storage immediately, rebuild context from storage on each execution
2. **Protocol/storage separation**: XML delimiters for LLM I/O, clean events in storage
3. **Stateless execution**: Agent and context assembly are pure functions, all state externalized to storage

Result: eliminates state corruption bugs, enables crash recovery, provides concurrent safety.

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

**Event mode (default):** Complete semantic units
```python
async for event in agent("Debug this code", stream="event"):
    if event["type"] == "think":
        print(f"~ {event['content']}")
    elif event["type"] == "respond":
        print(f"> {event['content']}")
```

**Token mode:** Real-time streaming
```python
async for event in agent("Debug this code", stream="token"):
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

- `read`, `write`, `edit`, `list`, `find`, `replace`
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

Events stored in storage layer (clean semantic units). Messages assembled for LLM (with protocol structure).

**Storage format (no delimiters):**
```python
{"type": "user", "content": "debug this"}
{"type": "think", "content": "checking logs"}
{"type": "call", "content": '{"name": "read", ...}'}
{"type": "result", "content": '[...]'}
```

**Assembly for LLM (with protocol):**
```python
[
  {"role": "system", "content": "PROTOCOL + TOOLS"},
  {"role": "user", "content": "debug this"},
  {"role": "assistant", "content": "<think>checking logs</think>\n<execute>[...]</execute>"},
  {"role": "user", "content": "<results>[...]</results>"}
]
```

**Context window control:**
- `history_window=None` - Full conversation history (default)
- `history_window=20` - Last 20 messages

Resume mode sends context once at connection. Replay mode rebuilds from storage per iteration.

## Multi-Provider Support

```python
agent = Agent(llm="openai")     # Realtime API (WebSocket)
agent = Agent(llm="gemini")     # Live API (WebSocket)
agent = Agent(llm="anthropic")  # HTTP only
```


## Memory System

**Profile learning (optional):**
```python
agent = Agent(llm="openai", profile=True)
# Learns patterns from interactions, embedded in system prompt
```

**Semantic search (agent-controlled):**
```python
agent = Agent(llm="openai", tools=[...])
# Agent can use recall tool to query past conversations
```

See [docs/protocol.md](docs/protocol.md) for execution protocol details.

## Documentation

- [architecture.md](docs/architecture.md) - Core pipeline and design decisions
- [protocol.md](docs/protocol.md) - Delimiter protocol specification
- [proof.md](docs/proof.md) - Mathematical efficiency analysis
- [tools.md](docs/tools.md) - Built-in tool reference

## License

Apache 2.0
