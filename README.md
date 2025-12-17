# Cogency

Streaming agents with stateless context assembly.

## Install

```bash
pip install cogency
export OPENAI_API_KEY="your-key"
```

## Quickstart

```python
from cogency import Agent

agent = Agent(llm="openai")
async for event in agent("What files are in this directory?"):
    if event["type"] == "respond":
        print(event["content"])
```

## Core Design

1. **Persist-then-rebuild**: Events written to storage immediately, context rebuilt each execution
2. **Protocol/storage separation**: XML delimiters for LLM I/O, clean events in storage
3. **Stateless execution**: Agent and context are pure functions, all state in storage

Result: no state corruption, crash recovery, concurrent safety.

## Execution Modes

| Mode | Method | Token Usage | Providers |
|------|--------|-------------|-----------|
| Resume | WebSocket | Constant | OpenAI, Gemini |
| Replay | HTTP | Grows with conversation | All |
| Auto | WebSocket with HTTP fallback | Optimal | All |

```python
agent = Agent(llm="openai", mode="auto")  # Default
```

**Token efficiency (Resume vs Replay):**

| Turns | Replay | Resume | Savings |
|-------|--------|--------|---------|
| 16 | 100,800 | 10,800 | 9.3x |
| 32 | 355,200 | 20,400 | 17.4x |

## Streaming

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

## Conversations

**Stateless (default):**
```python
async for event in agent("What's in this directory?"):
    if event["type"] == "respond":
        print(event["content"])
```

**Stateful with profile learning:**
```python
async for event in agent(
    "Continue our code review",
    conversation_id="review_session",
    user_id="developer"  # For profile learning and multi-tenancy
):
    if event["type"] == "respond":
        print(event["content"])
```

## Built-in Tools

| Tool | Description |
|------|-------------|
| `read` | Read file (with optional pagination) |
| `write` | Write file (overwrite protection) |
| `edit` | Replace exact text in file |
| `list` | Tree view of directory |
| `find` | Find files by pattern or content |
| `replace` | Find-and-replace across files |
| `shell` | Execute shell command |
| `search` | Web search |
| `scrape` | Extract webpage text |
| `recall` | Search past conversations |

## Custom Tools

```python
from dataclasses import dataclass
from typing import Annotated
from cogency import ToolResult
from cogency.core.tool import tool
from cogency.core.protocols import ToolParam

@dataclass
class QueryParams:
    sql: Annotated[str, ToolParam(description="SQL query")]

@tool("Execute SQL queries")
async def query_db(params: QueryParams, **kwargs) -> ToolResult:
    result = db.execute(params.sql)
    return ToolResult(outcome="Query executed", content=result)

agent = Agent(llm="openai", tools=[query_db])
```

## Configuration

```python
agent = Agent(
    llm="openai",                    # or "gemini", "anthropic"
    mode="auto",                     # "resume", "replay", or "auto"
    storage=custom_storage,          # Custom Storage implementation
    identity="Custom agent identity",
    instructions="Additional context",
    tools=[CustomTool()],
    max_iterations=10,
    history_window=None,             # None = full history, int = sliding window
    history_transform=compress,      # Optional history compression callable
    profile=True,                    # Enable automatic user learning
    security=Security(access="project", shell_timeout=60),  # Security policies
    notifications=notification_source,  # Mid-execution context injection
    debug=False
)
```

**History compression:** For long conversations, pass `history_transform` to compress context:

```python
async def compress(messages: list[dict]) -> list[dict]:
    if len(messages) <= 20:
        return messages
    return [{"role": "system", "content": f"[{len(messages)-10} earlier messages]"}] + messages[-10:]

agent = Agent(llm="openai", history_transform=compress)
```

## Documentation

- [architecture.md](docs/architecture.md) - Core pipeline and design decisions
- [execution.md](docs/execution.md) - Tool execution protocol specification
- [protocol.md](docs/protocol.md) - Wire format, event stream, storage
- [tools.md](docs/tools.md) - Built-in tool reference
- [memory.md](docs/memory.md) - Profile, recall, history window
- [proof.md](docs/proof.md) - Mathematical efficiency analysis

## License

Apache 2.0
