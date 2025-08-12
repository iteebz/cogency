# Configuration

Zero ceremony with sensible defaults.

## Agent Configuration

```python
from cogency import Agent

agent = Agent("assistant")  # All defaults

# Common config
agent = Agent(
    "assistant",
    tools=[Files(), Shell()],     # Specific tools (default: none)
    memory=True,                  # Memory (default: False)
    mode="deep",                  # Mode: "fast", "deep", "adapt" (default: "adapt")
    max_iterations=15,            # Max loops (default: 10)
    notify=False,                 # Progress display (default: True)
    identity="You are..."         # Custom prompt
)
```

## Parameters

### Core Parameters
- **`name`**: Agent identifier (default: "cogency")
- **`tools`**: List of Tool instances (default: `[]`)
- **`memory`**: Enable memory - `True` or `SituatedMemory` instance (default: `False`)
- **`handlers`**: Custom event handlers for streaming/websockets

### Behavior  
- **`identity`**: Custom system prompt
- **`mode`**: Reasoning mode - `"adapt"`, `"fast"`, `"deep"` (default: `"adapt"`)
- **`max_iterations`**: Max iterations (default: `10`)
- **`notify`**: Progress notifications (default: `True`)

## Memory Persistence

Auto-persists to SQLite:

```python
agent = Agent("assistant", memory=True)  # Persists across sessions
```

## Provider Configuration

```python
from cogency import Agent
from cogency.providers import OpenAI, Anthropic

# Auto-detect from environment
agent = Agent("assistant")  # Uses OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.

# Explicit provider
agent = Agent("assistant", llm=OpenAI(model="gpt-4o"))
agent = Agent("assistant", llm=Anthropic(model="claude-3-5-sonnet-20241022"))
```

## Environment Variables

Auto-detects providers:
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`  
- `GEMINI_API_KEY`
- `MISTRAL_API_KEY`
- `GROQ_API_KEY`
- `NOMIC_API_KEY`

## Directory Structure

Cogency stores data in `.cogency/` by default:
```
.cogency/
├── state/     # Agent state persistence
├── memory/    # User profiles and memory
└── logs/      # Execution traces
```

Override with `COGENCY_BASE_DIR` environment variable.

---

*Configuration for Cogency v1.2.2*