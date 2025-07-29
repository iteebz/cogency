# Agent Configuration Reference

**Version**: 1.0.0  
**Last Updated**: 2025-07-29

Detailed configuration objects for power users who need fine-grained control over Agent behavior.

## Configuration Objects

### Robust
Comprehensive robustness configuration (retry, checkpointing, persistence, circuit breaker, rate limiting):

```python
@dataclass
class Robust:
    # Core toggles
    retry: bool = True
    circuit: bool = True
    rate_limit: bool = True
    checkpoint: bool = True
    
    # Retry policy (from resilient-result)
    attempts: int = 3
    timeout: Optional[float] = None
    
    # Backoff strategy
    backoff: str = "exponential"  # "exponential", "linear", "fixed"
    backoff_delay: float = 0.1
    backoff_factor: float = 2.0
    backoff_max: float = 30.0
    
    # Circuit breaker
    circuit_failures: int = 5
    circuit_window: int = 300
    
    # Rate limiting
    rate_limit_rps: float = 10.0
    rate_limit_burst: Optional[int] = None
    
    # Checkpointing
    ckpt_max_age: int = 1
    ckpt_dir: Optional[str] = None

# Usage
from cogency import Robust

# Simple - change one thing
agent = Agent(robust=Robust(attempts=10))

# Production - multiple tweaks
agent = Agent(robust=Robust(
    timeout=120.0,
    ckpt_dir="/app/data",
    rate_limit_rps=2.0
))
```


### Observe
Observability/telemetry configuration for metrics collection:

```python
@dataclass
class Observe:
    # Metrics collection
    metrics: bool = True
    timing: bool = True
    counters: bool = True
    
    # Phase-specific telemetry
    phases: Optional[List[str]] = None  # ["reason", "act"] or None for all
    
    # Export configuration
    export_format: str = "prometheus"  # "prometheus", "json", "opentelemetry"
    export_endpoint: Optional[str] = None

# Usage
from cogency import Observe

agent = Agent(observe=Observe(
    metrics=True,
    phases=["reason", "act"],  # Only observe reasoning and tool execution
    export_format="opentelemetry"
))
```

### Persist
Configuration for state persistence:

```python
@dataclass
class Persist:
    enabled: bool = True
    backend: Optional[Any] = None  # Backend instance (e.g., FileBackend)

# Usage
from cogency import Persist

agent = Agent(persist=Persist(
    enabled=True,
    backend=CustomBackend()
))
```

## Advanced Examples

### Production Configuration
```python
from cogency import Robust, Observe

agent = Agent(
    "production-agent",
    robust=Robust(
        attempts=8,
        timeout=120.0,
        ckpt_dir="/var/lib/cogency/checkpoints",
        ckpt_max_age=24,
        rate_limit_rps=5.0,
        circuit_failures=3
    ),
    observe=Observe(
        phases=["reason", "act", "respond"],
        export_format="opentelemetry",
        export_endpoint="http://jaeger:14268/api/traces"
    ),
    persist=Persist(
        backend=PostgresBackend(connection_string="...")
    )
)
```

### Development Configuration
```python
from cogency import Robust

# Faster iteration, more aggressive checkpointing
agent = Agent(
    "dev-agent",
    debug=True,
    robust=Robust(
        attempts=2, 
        timeout=10.0,  # Fail fast
        ckpt_max_age=0.1  # 6 minute expiry
    ),
    persist=False,  # No persistence overhead
    observe=False   # No telemetry overhead
)
```

## Migration from Old API

```python
# Old API (deprecated)
agent = Agent(robust=True, observe=True)

# New API (recommended)
agent = Agent(robust=True, observe=True)

# Or with configs
agent = Agent(
    robust=Robust(attempts=5, rate_limit_rps=2.0),
    observe=Observe(phases=["reason"])
)
```

---

**See [Agent API](./agent-api.md) for the main constructor specification.**