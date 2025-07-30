# Configuration

Advanced configuration for production deployments and specialized use cases.

## Configuration Objects

Cogency uses configuration objects for advanced features. Default boolean values work for 90% of use cases.

### Robust Configuration

```python
from cogency import Robust

# Simple usage
agent = Agent(robust=True)   # Default settings
agent = Agent(robust=False)  # Disable robustness

# Advanced configuration
agent = Agent(robust=Robust(
    attempts=5,
    timeout=60.0,
    backoff="exponential",
    rate_limit_rps=10.0
))
```

### Observe Configuration

```python
from cogency import Observe

# Simple usage
agent = Agent(observe=True)   # Basic telemetry

# Advanced configuration
agent = Agent(observe=Observe(
    metrics=True,
    phases=["reason", "act"],
    export_format="prometheus"
))
```

### Persist Configuration

```python
from cogency import Persist

# Simple usage
agent = Agent(persist=True)   # Default file-based persistence

# Advanced configuration
agent = Agent(persist=Persist(
    enabled=True,
    backend=CustomBackend()
))
```

## Production Examples

### High-Availability Setup
```python
from cogency import Robust, Observe, Persist

agent = Agent(
    "production-agent",
    robust=Robust(attempts=5, timeout=120.0, rate_limit_rps=5.0),
    observe=Observe(metrics=True, export_format="prometheus"),
    persist=Persist(backend=RedisBackend())
)
```

### Development Setup
```python
agent = Agent(
    "dev-agent",
    debug=True,
    notify=True,
    mode="fast",
    depth=5,
    robust=Robust(attempts=2, timeout=10.0)
)
```

### Research Agent
```python
agent = Agent(
    "researcher",
    mode="deep",
    depth=20,
    notify=True,
    robust=Robust(timeout=180.0, rate_limit_rps=2.0)
)
```

## Custom Backends

### Custom Memory Backend
```python
from cogency.memory import Store

class CustomMemory(Store):
    async def save(self, content: str, metadata: dict = None):
        # Custom save logic
        pass
    
    async def search(self, query: str, limit: int = 5) -> list:
        # Custom search logic
        return []

agent = Agent(memory=CustomMemory())
```

### Custom LLM Backend
```python
from cogency.services import LLM

class CustomLLM(LLM):
    async def complete(self, messages: list, **kwargs) -> str:
        return "response"
    
    async def stream(self, messages: list, **kwargs):
        yield "chunk"

agent = Agent(llm=CustomLLM())
```

## Environment Variables

```bash
# LLM Provider
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
export GEMINI_API_KEY=your-key

# Memory
export COGENCY_MEMORY_DIR=./custom_memory

# Metrics
export COGENCY_METRICS_ENDPOINT=http://prometheus:9090
```

## Performance Tuning

### Latency Optimization
```python
agent = Agent(
    mode="fast",
    depth=3,
    robust=Robust(attempts=1, timeout=10.0)
)
```

### Quality Optimization
```python
agent = Agent(
    mode="deep",
    depth=25,
    robust=Robust(attempts=5, timeout=300.0)
)
```

---

*Advanced configuration for production deployments and specialized use cases.*