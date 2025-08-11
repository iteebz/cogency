# Configuration

Zero ceremony configuration with sensible defaults.

## Agent Configuration

```python
from cogency import Agent

# Zero ceremony - all defaults
agent = Agent("assistant")

# Common configuration
agent = Agent(
    "assistant",
    tools=[Files(), Shell()],     # Specific tools (default: none)
    memory=True,                  # Enable memory (default: False)
    mode="deep",                  # Reasoning mode: "fast", "deep", "adapt" (default: "adapt")
    max_iterations=15,            # Max reasoning loops (default: 10)
    notify=False,                 # Disable progress display (default: True)
    identity="You are..."         # Custom system prompt
)
```

## Parameters

### Core Parameters
- **`name`**: Agent identifier (default: "cogency")
- **`tools`**: List of Tool instances (default: `[]`)
- **`memory`**: Enable memory - `True` or `SituatedMemory` instance (default: `False`)
- **`handlers`**: Custom event handlers for streaming/websockets

### Behavior Parameters  
- **`identity`**: Custom system prompt for personality
- **`mode`**: Reasoning mode - `"adapt"`, `"fast"`, or `"deep"` (default: `"adapt"`)
- **`max_iterations`**: Max reasoning iterations (default: `10`)
- **`notify`**: Enable progress notifications (default: `True`)

## Memory Persistence

Memory automatically persists to SQLite:

```python
# Memory automatically persists across sessions
agent = Agent("assistant", memory=True)
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

Cogency auto-detects providers from environment:
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

*Production-ready configuration for Cogency v1.3.0*