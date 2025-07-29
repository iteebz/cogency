# Agent API v1.0 Specification

**Status**: Final v1.0 API Design  
**Version**: 1.0.0  
**Last Updated**: 2025-07-29

## Philosophy: Zero Ceremony + Progressive Disclosure

```python
# 90% of users - just works
agent = Agent()

# 9% of users - simple overrides  
agent = Agent(notify=False, llm=my_llm)

# 1% of users - full control
agent = Agent("expert", robust=Robust(attempts=10, rate_limit_rps=2.0))
```

## Constructor Signature

```python
def __init__(
    self,
    name: str = "cogency",
    *,
    # Backend Systems
    llm: Optional[Any] = None,
    tools: Optional[Any] = None,
    memory: Optional[Any] = None,
    
    # Agent Personality
    prompt: Optional[str] = None,
    identity: Optional[str] = None,
    output_schema: Optional[Any] = None,
    
    # Execution Control
    mode: Literal["fast", "deep", "adapt"] = "adapt",
    depth: int = 10,
    
    # User Feedback
    notify: bool = True,
    debug: bool = False,
    
    # System Behaviors (@phase decorator control)
    robust: Union[bool, Robust] = True,
    observe: Union[bool, Observe] = False,
    persist: Union[bool, Persist] = False,
    
    # Integrations
    mcp: bool = False,
) -> None:
```

## Key Parameters

### System Behaviors
Controls `@phase` decorator behavior with Bool|Config pattern:

- **`robust`**: `True`|`False`|`Robust(attempts=5)` - retry/rate_limit/circuit/checkpoint logic
- **`observe`**: `False`|`True`|`Observe(phases=["reason"])` - Telemetry collection  
- **`persist`**: `False`|`True`|`Persist(backend=custom)` - State persistence

### Core Settings
- **`mode`**: `"fast"`|`"deep"`|`"adapt"` - Reasoning depth
- **`llm`**: Auto-detects OpenAI/Anthropic or custom backend
- **`notify`**: Show execution progress (default: True)
- **`debug`**: Detailed tracing (default: False)

## Configuration Objects

```python
from cogency.config import Robust, Observe

# Power user configs
agent = Agent(
    robust=Robust(attempts=5, timeout=60.0, rate_limit_rps=2.0),
    observe=Observe(phases=["reason", "act"], export_format="prometheus"),
    persist=Persist(backend=CustomBackend())
)
```

See [Configuration Reference](./agent-config.md) for full config object specs.

## Usage Examples

```python
# Zero ceremony (90% of users)
agent = Agent()

# Simple overrides (9% of users)  
agent = Agent(notify=False, mode="deep")
agent = Agent(llm=MyCustomLLM(), observe=True)

# Power users (1% of users)
agent = Agent(
    "production-agent",
    llm=CustomLLM(),
    robust=Robust(attempts=8, timeout=120.0, rate_limit_rps=5.0),
    observe=Observe(phases=["reason"], export_format="opentelemetry"),
    persist=Persist(backend=PostgresBackend())
)
```

## Internal Architecture

### @phase Decorator Pattern
Agent constructor controls unified `@phase` decorator via feature flags:

```python
# Phase methods with beautiful IDE autocomplete
@phase.reason()    # Uses robust=True, observe=False, etc.
@phase.act()       # Based on Agent constructor params
@phase.preprocess()
@phase.respond()

# Implementation:
class _PhaseDecorators:
    reason = staticmethod(_phase_factory("reasoning", True, Retry.api()))
    act = staticmethod(_phase_factory("tool_execution", True, Retry.db()))
    # etc...
    
phase = _PhaseDecorators()
```

### Config Organization
```
cogency/config/
├── robust.py     # @dataclass Robust (retry, circuit, rate_limit, checkpoint, persist)
└── observe.py    # @dataclass Observe (profiling, metrics)
```

---

**This is the definitive v1.0 Agent API specification.**