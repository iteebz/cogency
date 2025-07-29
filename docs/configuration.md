# Configuration

Advanced configuration options for production deployments and specialized use cases.

## Configuration Objects

Cogency uses configuration objects for advanced features that most users don't need. The default boolean values work for 90% of use cases.

### Robust Configuration

Error handling, retry logic, and resilience features.

```python
from cogency import Robust

# Simple usage
agent = Agent(robust=True)   # Default settings
agent = Agent(robust=False)  # Disable robustness features

# Advanced configuration
agent = Agent(robust=Robust(
    attempts=5,              # Retry attempts
    timeout=60.0,            # Timeout in seconds
    backoff="exponential",   # Backoff strategy
    backoff_delay=0.1,       # Initial delay
    backoff_factor=2.0,      # Backoff multiplier
    backoff_max=30.0,        # Maximum delay
    rate_limit_rps=10.0,     # Rate limiting (requests per second)
    circuit_failures=5,      # Circuit breaker failure threshold
    circuit_window=300       # Circuit breaker time window
))
```

#### Robust Parameters

**`attempts`** (`int`, default: `3`)
- Number of retry attempts for failed operations

**`timeout`** (`float`, default: `None`)
- Timeout in seconds for individual operations

**`backoff`** (`str`, default: `"exponential"`)
- Backoff strategy: `"exponential"`, `"linear"`, or `"fixed"`

**`backoff_delay`** (`float`, default: `0.1`)
- Initial delay between retries in seconds

**`backoff_factor`** (`float`, default: `2.0`)
- Multiplier for exponential backoff

**`backoff_max`** (`float`, default: `30.0`)
- Maximum delay between retries

**`rate_limit_rps`** (`float`, default: `10.0`)
- Rate limiting in requests per second

**`circuit_failures`** (`int`, default: `5`)
- Number of failures before circuit breaker opens

**`circuit_window`** (`int`, default: `300`)
- Time window for circuit breaker in seconds

### Observe Configuration

Telemetry, metrics, and monitoring features.

```python
from cogency import Observe

# Simple usage
agent = Agent(observe=False)  # No telemetry (default)
agent = Agent(observe=True)   # Basic telemetry

# Advanced configuration
agent = Agent(observe=Observe(
    metrics=True,                    # Collect metrics
    timing=True,                     # Collect timing data
    counters=True,                   # Collect counters
    phases=["reason", "act"],        # Which phases to observe
    export_format="prometheus",      # Export format
    export_endpoint="http://..."     # Export endpoint
))
```

#### Observe Parameters

**`metrics`** (`bool`, default: `True`)
- Enable metrics collection

**`timing`** (`bool`, default: `True`)
- Collect timing information for operations

**`counters`** (`bool`, default: `True`)
- Collect counter metrics

**`phases`** (`List[str]`, default: `None`)
- Which phases to observe. `None` means all phases.
- Options: `["preprocess", "reason", "act", "respond"]`

**`export_format`** (`str`, default: `"prometheus"`)
- Metrics export format: `"prometheus"`, `"json"`, `"opentelemetry"`

**`export_endpoint`** (`str`, default: `None`)
- Endpoint URL for metrics export

### Persist Configuration

State persistence across sessions.

```python
from cogency import Persist

# Simple usage
agent = Agent(persist=False)  # No persistence (default)
agent = Agent(persist=True)   # Default file-based persistence

# Advanced configuration
agent = Agent(persist=Persist(
    enabled=True,
    backend=CustomBackend()  # Custom persistence backend
))
```

#### Persist Parameters

**`enabled`** (`bool`, default: `True`)
- Enable state persistence

**`backend`** (`Any`, default: `None`)
- Custom persistence backend instance

## Production Configuration Examples

### High-Availability Setup
```python
from cogency import Robust, Observe, Persist

agent = Agent(
    "production-agent",
    robust=Robust(
        attempts=5,
        timeout=120.0,
        rate_limit_rps=5.0,
        circuit_failures=3,
        circuit_window=600
    ),
    observe=Observe(
        metrics=True,
        phases=["reason", "act", "respond"],
        export_format="prometheus",
        export_endpoint="http://prometheus:9090/metrics"
    ),
    persist=Persist(
        enabled=True,
        backend=RedisBackend("redis://redis:6379")
    )
)
```

### Development Setup
```python
# Fast iteration, detailed debugging
agent = Agent(
    "dev-agent",
    debug=True,              # Detailed tracing
    notify=True,             # Show progress
    mode="fast",             # Quick responses
    depth=5,                 # Limit iterations
    robust=Robust(
        attempts=2,          # Fail fast
        timeout=10.0         # Short timeout
    ),
    observe=False,           # No telemetry overhead
    persist=False            # No persistence overhead
)
```

### Research Agent Setup
```python
# Deep analysis, comprehensive logging
agent = Agent(
    "researcher",
    mode="deep",             # Always use deep reasoning
    depth=20,                # Allow long reasoning chains
    notify=True,             # Show reasoning progress
    robust=Robust(
        attempts=3,
        timeout=180.0,       # Generous timeout for research
        rate_limit_rps=2.0   # Conservative rate limiting
    ),
    observe=Observe(
        metrics=True,
        phases=["reason"],   # Focus on reasoning metrics
        export_format="json"
    )
)
```

### High-Volume API Setup
```python
# Optimized for throughput
agent = Agent(
    "api-agent",
    mode="fast",             # Prioritize speed
    depth=3,                 # Limit reasoning depth
    notify=False,            # Clean logs
    debug=False,             # No debug overhead
    robust=Robust(
        attempts=2,          # Quick failure
        timeout=30.0,        # Fast timeout
        rate_limit_rps=20.0  # High throughput
    ),
    observe=Observe(
        metrics=True,
        timing=True,
        phases=["act"],      # Monitor tool execution only
        export_format="prometheus"
    )
)
```

## Custom Backends

### Custom Persistence Backend
```python
from cogency.persist import StateBackend

class CustomPersistBackend(StateBackend):
    async def save(self, key: str, state: dict, metadata: dict):
        # Custom save logic
        pass
    
    async def load(self, key: str) -> tuple:
        # Custom load logic
        return state_dict, metadata_dict
    
    async def delete(self, key: str):
        # Custom delete logic
        pass

# Usage
agent = Agent(persist=Persist(backend=CustomPersistBackend()))
```

### Custom Memory Backend
```python
from cogency.memory import Store

class CustomMemory(Store):
    async def save(self, content: str, metadata: dict = None):
        # Custom memory save logic
        pass
    
    async def search(self, query: str, limit: int = 5) -> list:
        # Custom memory search logic
        return []
    
    async def clear(self):
        # Custom memory clear logic
        pass

# Usage
agent = Agent(memory=CustomMemory())
```

### Custom LLM Backend
```python
from cogency.services import LLM

class CustomLLM(LLM):
    async def complete(self, messages: list, **kwargs) -> str:
        # Custom LLM completion logic
        return "response"
    
    async def stream(self, messages: list, **kwargs):
        # Custom streaming logic
        yield "chunk"

# Usage
agent = Agent(llm=CustomLLM())
```

## Environment Variables

### LLM Configuration
```bash
# OpenAI
export OPENAI_API_KEY=sk-...
export OPENAI_MODEL=gpt-4  # Optional

# Anthropic
export ANTHROPIC_API_KEY=sk-ant-...
export ANTHROPIC_MODEL=claude-3-sonnet-20240229  # Optional

# Google Gemini
export GEMINI_API_KEY=your-key
export GEMINI_MODEL=gemini-pro  # Optional

# xAI Grok
export GROK_API_KEY=xai-...
export GROK_MODEL=grok-beta  # Optional

# Mistral
export MISTRAL_API_KEY=your-key
export MISTRAL_MODEL=mistral-large-latest  # Optional
```

### Memory Configuration
```bash
# Memory directory
export COGENCY_MEMORY_DIR=./custom_memory

# Memory backend
export COGENCY_MEMORY_BACKEND=filesystem  # or redis, postgres, etc.
```

### Observability Configuration
```bash
# Prometheus metrics
export COGENCY_METRICS_ENDPOINT=http://prometheus:9090/metrics
export COGENCY_METRICS_FORMAT=prometheus

# OpenTelemetry
export OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:14268/api/traces
export OTEL_SERVICE_NAME=cogency-agent
```

## Configuration Validation

### Validate Configuration
```python
from cogency import Agent, Robust

try:
    agent = Agent(robust=Robust(
        attempts=0,  # Invalid: must be > 0
        timeout=-1   # Invalid: must be positive
    ))
except ValueError as e:
    print(f"Configuration error: {e}")
```

### Configuration Debugging
```python
# Enable configuration debugging
agent = Agent(debug=True)

# Configuration is logged during agent creation
# Shows: LLM provider, memory backend, tool count, etc.
```

## Performance Tuning

### Latency Optimization
```python
# Minimize latency
agent = Agent(
    mode="fast",
    depth=3,
    robust=Robust(attempts=1, timeout=10.0),
    observe=False,
    persist=False
)
```

### Throughput Optimization
```python
# Maximize throughput
agent = Agent(
    notify=False,
    debug=False,
    robust=Robust(rate_limit_rps=50.0),
    observe=Observe(phases=["act"])  # Minimal observability
)
```

### Quality Optimization
```python
# Maximize quality
agent = Agent(
    mode="deep",
    depth=25,
    robust=Robust(
        attempts=5,
        timeout=300.0,
        rate_limit_rps=1.0
    )
)
```

---

*Advanced configuration enables production deployments and specialized use cases while maintaining simplicity for common usage.*