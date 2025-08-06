# Configuration

Cogency uses a **progressive disclosure** API design: simple boolean flags for beginners, detailed configuration objects for experts.

## Basic Configuration

```python
from cogency import Agent, Files, Shell

# Simple: boolean flags enable defaults
agent = Agent("assistant", memory=True, robust=True, observe=True)

# Advanced: specific configuration objects  
agent = Agent(
    "assistant",
    mode="deep",                  # "fast" | "deep" | "adapt" 
    max_iterations=10,                     # Max reasoning iterations
    debug=True,                   # Detailed tracing
    notify=True,                  # Progress notifications
    tools=[Files(), Shell()],     # Specific tools
    identity="You are..."         # Custom system prompt
)
```

## Memory Configuration

```python
from cogency import Agent, MemoryConfig

# Simple: enable with defaults
agent = Agent("assistant", memory=True)

# Advanced: custom settings
agent = Agent(
    "assistant",
    memory=MemoryConfig(
        persist=True,
        synthesis_threshold=8000,
        user_id="alice"
    )
)
```

## Robustness Configuration

```python
from cogency import Agent, RobustConfig

# Simple: enable with defaults
agent = Agent("assistant", robust=True)

# Advanced: custom retry/timeout settings
agent = Agent(
    "assistant", 
    robust=RobustConfig(
        retry=True,
        attempts=5,
        timeout=120.0,
        rate_limit_rps=2.0
    )
)
```

## Observability Configuration

```python
from cogency import Agent, ObserveConfig

# Simple: enable with defaults
agent = Agent("assistant", observe=True)

# Advanced: custom monitoring
agent = Agent(
    "assistant",
    observe=ObserveConfig(
        metrics=True,
        export_format="prometheus",
        steps=["reason", "act"]
    )
)
```

## Progressive Disclosure Principle

This Union pattern serves different user intents:

- **Beginners**: Use boolean flags (`memory=True`) for quick starts
- **Experts**: Use config objects (`memory=MemoryConfig(...)`) for precision

Both patterns are validated to prevent conflicting configurations.

## Environment Variables

```bash
# LLM Providers
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...  
export GEMINI_API_KEY=your-key
```

## Performance Profiles

**Fastest:**
```python
agent = Agent(mode="fast", max_iterations=3, notify=False, robust=False)
```

**Most accurate:**
```python  
agent = Agent(mode="deep", max_iterations=25, memory=True, robust=True)
```

**Production:**
```python
agent = Agent(
    mode="adapt", 
    memory=True, 
    robust=RobustConfig(attempts=5, timeout=120.0),
    observe=True
)
```

---

*Production-ready configuration for Cogency v1.0.0*