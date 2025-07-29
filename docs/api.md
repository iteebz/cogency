# Agent API Reference

Complete documentation for the `Agent` class.

## Constructor

```python
Agent(
    name: str = "cogency",
    *,
    # Backend Systems
    llm: Optional[LLM] = None,
    embed: Optional[Embed] = None, 
    tools: Optional[List[Tool]] = None,
    memory: Optional[Store] = None,
    # Agent Personality
    identity: Optional[str] = None,
    output_schema: Optional[Dict[str, Any]] = None,
    # Execution Control
    mode: Literal["fast", "deep", "adapt"] = "adapt",
    depth: int = 10,
    # User Feedback
    notify: bool = True,
    debug: bool = False,
    # System Behaviors
    robust: Union[bool, Robust] = True,
    observe: Union[bool, Observe] = False,
    persist: Union[bool, Persist] = False,
    # Integrations
    mcp: bool = False,
)
```

### Parameters

#### Basic Configuration

**`name`** (`str`, default: `"cogency"`)
- Agent identifier for logging and debugging

**`mode`** (`"fast" | "deep" | "adapt"`, default: `"adapt"`)
- Reasoning mode:
  - `"fast"`: Direct execution for simple queries
  - `"deep"`: Reflection and planning for complex tasks  
  - `"adapt"`: Automatically choose based on query complexity

**`depth`** (`int`, default: `10`)
- Maximum reasoning iterations before stopping

#### Backend Systems

**`llm`** (`Optional[LLM]`, default: `None`)
- Custom LLM instance. Auto-detects from environment if not provided.

**`tools`** (`Optional[List[Tool]]`, default: `None`)  
- Custom tools list. Uses built-in tools if not provided.

**`memory`** (`Optional[Store]`, default: `None`)
- Custom memory backend. Uses filesystem backend if not provided.

**`embed`** (`Optional[Embed]`, default: `None`)
- Custom embedding model for memory operations.

#### Agent Personality

**`identity`** (`Optional[str]`, default: `None`)
- Custom system prompt to define agent personality and behavior.

**`output_schema`** (`Optional[Dict[str, Any]]`, default: `None`)
- JSON schema for structured output format.

#### User Feedback

**`notify`** (`bool`, default: `True`)
- Show execution progress and tool usage.

**`debug`** (`bool`, default: `False`)
- Enable detailed execution tracing.

#### System Behaviors

**`robust`** (`Union[bool, Robust]`, default: `True`)
- Error handling and retry configuration:
  - `True`: Default retry and error handling
  - `False`: Disable robustness features
  - `Robust(...)`: Custom configuration

**`observe`** (`Union[bool, Observe]`, default: `False`)
- Telemetry and metrics collection:
  - `False`: No telemetry
  - `True`: Basic metrics
  - `Observe(...)`: Custom configuration

**`persist`** (`Union[bool, Persist]`, default: `False`)
- State persistence across sessions:
  - `False`: No persistence
  - `True`: Default file-based persistence
  - `Persist(...)`: Custom backend

**`mcp`** (`bool`, default: `False`)
- Enable Model Context Protocol server integration.

## Methods

### `async run(query: str, user_id: str = "default") -> str`

Execute a query and return the complete response.

**Parameters:**
- `query`: The user's question or request
- `user_id`: User identifier for conversation isolation

**Returns:** Complete agent response as a string

**Example:**
```python
result = await agent.run("What's the weather in London?")
print(result)  # "The weather in London is sunny, 18°C"
```

### `async stream(query: str, user_id: str = "default") -> AsyncIterator[str]`

Stream agent execution with real-time progress updates.

**Parameters:**
- `query`: The user's question or request  
- `user_id`: User identifier for conversation isolation

**Returns:** Async iterator yielding execution chunks

**Example:**
```python
async for chunk in agent.stream("Plan a trip to Tokyo"):
    print(chunk, end="", flush=True)
```

### `traces() -> List[Dict[str, Any]]`

Get detailed execution traces from the last run (debug mode only).

**Returns:** List of execution trace dictionaries

**Example:**
```python
agent = Agent(debug=True)
await agent.run("Calculate 2+2")
traces = agent.traces()
for trace in traces:
    print(f"{trace['phase']}: {trace['message']}")
```

## Configuration Objects

### Robust

Advanced error handling and retry configuration:

```python
from cogency import Robust

agent = Agent(robust=Robust(
    attempts=5,           # Retry attempts
    timeout=60.0,         # Timeout in seconds
    backoff="exponential", # Backoff strategy
    rate_limit_rps=2.0    # Rate limiting
))
```

### Observe

Telemetry and metrics configuration:

```python
from cogency import Observe

agent = Agent(observe=Observe(
    metrics=True,         # Collect metrics
    phases=["reason"],    # Which phases to observe
    export_format="json"  # Export format
))
```

### Persist

State persistence configuration:

```python
from cogency import Persist

agent = Agent(persist=Persist(
    enabled=True,
    backend=CustomBackend()  # Custom persistence backend
))
```

## Usage Examples

### Basic Agent
```python
agent = Agent("assistant")
result = await agent.run("What's 2+2?")
```

### Custom Configuration
```python
agent = Agent(
    "research-agent",
    mode="deep",
    notify=False,
    debug=True,
    depth=20
)
```

### Production Configuration
```python
from cogency import Robust, Observe

agent = Agent(
    "production-agent",
    robust=Robust(attempts=5, timeout=120.0),
    observe=Observe(metrics=True, export_format="prometheus"),
    persist=True
)
```

### Custom Tools
```python
from cogency.tools import Tool, tool

@tool
class CustomTool(Tool):
    def __init__(self):
        super().__init__("custom", "Custom functionality")
    
    async def run(self, param: str):
        return {"result": f"Custom: {param}"}

agent = Agent("assistant", tools=[CustomTool()])
```

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

agent = Agent("assistant", memory=CustomMemory())
```

## Error Handling

All methods handle errors gracefully and return error messages when execution fails:

```python
try:
    result = await agent.run("Invalid query that might fail")
except Exception as e:
    print(f"Agent execution failed: {e}")
```

For more robust error handling, use the `robust` configuration:

```python
agent = Agent(robust=Robust(attempts=3, timeout=30.0))
```

---

*See [Configuration](configuration.md) for detailed configuration options.*