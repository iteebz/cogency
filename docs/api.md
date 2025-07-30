# Agent API

```python
from cogency import Agent

# Zero ceremony
agent = Agent("assistant")
result = await agent.run("What's 2+2?")

# Full configuration
agent = Agent(
    "researcher",
    mode="deep",           # "fast" | "deep" | "adapt" 
    depth=10,             # Max reasoning iterations
    identity="You are...", # Custom system prompt
    robust=True,          # Retry + error handling
    observe=True,         # Metrics + tracing
    persist=True,         # State persistence
    debug=True            # Detailed logging
)
```

## Parameters

- **`mode`**: `"fast"` (direct) | `"deep"` (reflection) | `"adapt"` (auto-switch)
- **`depth`**: Max reasoning iterations (default: 10)
- **`identity`**: Custom system prompt for personality
- **`robust`**: Error handling + retry (bool or `Robust()` config)
- **`observe`**: Metrics collection (bool or `Observe()` config) 
- **`persist`**: State persistence (bool or `Persist()` config)
- **`debug`**: Detailed execution tracing

## Methods

```python
# Execute and return complete response
result = await agent.run("What's 2+2?", user_id="alice")

# Stream execution with real-time progress
async for chunk in agent.stream("Research quantum computing"):
    print(chunk, end="", flush=True)

# Get execution traces (debug mode only)
agent = Agent(debug=True)
await agent.run("Calculate something")
traces = agent.traces()  # List of phase execution details
```

## Advanced Configuration

```python
from cogency import Agent, Robust, Observe, Persist

# Production setup
agent = Agent(
    "production-agent",
    robust=Robust(
        attempts=5,
        timeout=120.0,
        backoff="exponential",
        rate_limit_rps=2.0
    ),
    observe=Observe(
        metrics=True,
        phases=["reason", "act"],
        export_format="prometheus"
    ),
    persist=Persist(
        enabled=True,
        backend=CustomBackend()
    )
)
```

## Custom Backends

```python
# Custom LLM provider
from cogency.services import LLM

class CustomLLM(LLM):
    async def _run_impl(self, messages, **kwargs) -> str:
        return "response"
    
    async def stream(self, messages, **kwargs):
        yield "chunk"

agent = Agent(llm=CustomLLM("custom"))

# Custom memory backend  
from cogency.memory import Store

class CustomMemory(Store):
    async def _store(self, artifact, embedding, **kwargs):
        # Save logic
        pass
    
    async def _read(self, **kwargs):
        # Retrieve logic
        return []

agent = Agent(memory=CustomMemory())
```