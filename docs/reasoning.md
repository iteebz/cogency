# Adaptive Reasoning

Cogency agents automatically adjust their thinking depth based on task complexity.

## Core Concept

**Adaptive reasoning** means agents discover task complexity during execution and adjust their cognitive approach automatically.

- **Fast mode**: Direct reasoning for simple queries
- **Deep mode**: Reflection and planning for complex tasks  
- **Adaptive mode**: Automatic switching based on task analysis

## Reasoning Modes

### Fast Mode
```python
agent = Agent("assistant", mode="fast")
await agent.run("What's 2+2?")
# � Direct response without deep reflection
```

**Characteristics:**
- Single reasoning pass
- Minimal tool orchestration
- Quick responses
- Best for: simple questions, calculations, direct queries

### Deep Mode
```python
agent = Agent("assistant", mode="deep")
await agent.run("Analyze this codebase and suggest improvements")
# � Multi-step analysis with reflection and planning
```

**Characteristics:**
- Multi-step reasoning with reflection
- Complex tool orchestration
- Thorough analysis
- Best for: analysis, planning, complex problem solving

### Adaptive Mode (Default)
```python
agent = Agent("assistant", mode="adapt")  # or just Agent("assistant")
await agent.run("Any query")
# � Automatically chooses appropriate depth
```

**Characteristics:**
- Task complexity analysis in prepare phase
- Automatic mode selection
- Zero configuration required
- Best for: general-purpose agents

## How It Works

### 4-Step Execution Loop

1. **Prepare**: Evaluates task complexity and selects reasoning mode
2. **Reason**: Applies selected reasoning depth (fast or deep)
3. **Act**: Executes tools with automatic retry
4. **Respond**: Formats response with identity awareness

### Complexity Analysis

The prepare phase analyzes:
- Query structure and intent
- Required tool orchestration
- Context complexity
- Domain expertise needed

### Mode Switching

```python
# These queries trigger different modes automatically:

# Simple � Fast mode
await agent.run("What's the weather?")

# Complex � Deep mode  
await agent.run("Build a production API with authentication, database, and tests")
```

## Configuration

### Reasoning Depth
```python
agent = Agent(
    "assistant",
    max_iterations=20,      # Max reasoning iterations
    mode="deep"    # Force deep reasoning
)
```

### Early Termination
```python
agent = Agent(
    "assistant", 
    max_iterations=3,       # Limited iterations
    mode="fast"    # Prefer speed over thoroughness
)
```

## Streaming Reasoning

Watch agents think in real-time:

```python
async for chunk in agent.stream("Complex analysis task"):
    print(chunk, end="", flush=True)
```

Output shows reasoning progression:
```
=' prepare: Complex task detected � escalating to deep mode
>� reason: Analyzing requirements...
>� reason: Planning approach...
=� files(action='read', path='config.py') � Configuration loaded
>� reason: Reflection � Need to check dependencies
=� shell(command='pip list') � Dependencies listed
>� reason: Final analysis...
> Based on my analysis...
```

## Best Practices

### Let Adaptive Mode Work
```python
# Recommended - let agent choose
agent = Agent("assistant")  # mode="adapt" by default

# Override only when needed
agent = Agent("assistant", mode="fast")  # For speed-critical apps
agent = Agent("assistant", mode="deep")  # For analysis-heavy tasks
```

### Depth Configuration
```python
# Production: balance quality and speed
agent = Agent("assistant", max_iterations=10)

# Development: faster iteration
agent = Agent("assistant", max_iterations=5, mode="fast")

# Research: thorough analysis
agent = Agent("assistant", max_iterations=25, mode="deep")
```

### Memory Integration
```python
# Memory enhances reasoning quality
agent = Agent("assistant", memory=True)
# Agent remembers context and preferences for better reasoning
```

## Performance Characteristics

| Mode | Latency | Quality | Use Case |
|------|---------|---------|----------|
| Fast | Low | Good | Simple queries, quick responses |
| Deep | High | Excellent | Analysis, planning, complex tasks |
| Adapt | Variable | Optimal | General-purpose (recommended) |

## Examples

### Research Assistant
```python
agent = Agent("researcher", mode="deep", max_iterations=20)
await agent.run("Research renewable energy trends and create a comprehensive report")
# � Deep analysis with multiple reasoning passes
```

### Chat Bot
```python
agent = Agent("chatbot", mode="fast", max_iterations=3)
await agent.run("Hello, how are you?")
# � Quick, friendly response
```

### Code Assistant
```python
agent = Agent("coder", mode="adapt")
await agent.run("Fix this bug: [code snippet]")
# � Automatically chooses appropriate depth based on complexity
```

---

*Adaptive reasoning architecture for Cogency v1.0.0*