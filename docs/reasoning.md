# Adaptive Reasoning

Agents adjust thinking depth based on task complexity.

## Core Concept

Agents discover task complexity during execution and adjust approach automatically.

- **Fast mode**: Direct reasoning for simple queries
- **Deep mode**: Reflection and planning for complex tasks  
- **Adaptive mode**: Automatic switching based on task analysis

## Reasoning Modes

### Fast Mode
```python
agent = Agent("assistant", mode="fast")
agent.run("What's 2+2?")
# Direct response
```

**Characteristics:**
- Single reasoning pass
- Minimal tool orchestration
- Quick responses
- Best for: simple questions, calculations, direct queries

### Deep Mode
```python
agent = Agent("assistant", mode="deep")
agent.run("Analyze this codebase and suggest improvements")
# Multi-step analysis with reflection
```

**Characteristics:**
- Multi-step reasoning with reflection
- Complex tool orchestration
- Thorough analysis
- Best for: analysis, planning, complex problem solving

### Adaptive Mode (Default)
```python
agent = Agent("assistant", mode="adapt")  # or just Agent("assistant")
agent.run("Any query")
# Auto-chooses depth
```

**Characteristics:**
- Task complexity analysis in triage step
- Automatic mode selection
- Zero configuration
- Best for: general-purpose agents

## How It Works

### 4-Step Execution Loop

1. **Triage**: Evaluates complexity, selects mode
2. **Reason**: Applies reasoning depth (fast or deep)
3. **Act**: Executes tools with retry
4. **Respond**: Formats response

### Complexity Analysis

Triage analyzes:
- Query structure and intent
- Tool orchestration needed
- Context complexity
- Domain expertise required

### Mode Switching

```python
# Auto-triggers different modes:

# Simple → Fast mode
agent.run("What's the weather?")

# Complex → Deep mode  
agent.run("Build a production API with auth, database, and tests")
```

## Configuration

### Reasoning Depth
```python
agent = Agent(
    "assistant",
    max_iterations=20,      # Max iterations
    mode="deep"    # Force deep
)
```

### Early Termination
```python
agent = Agent(
    "assistant", 
    max_iterations=3,       # Limited iterations
    mode="fast"    # Prefer speed
)
```

## Streaming Reasoning

Watch agents think in real-time:

```python
async for chunk in agent.stream("Complex analysis task"):
    print(chunk, end="", flush=True)
```

Shows reasoning progression:
```
=' triage: Complex task detected � escalating to deep mode
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
# Let agent choose
agent = Agent("assistant")  # mode="adapt" by default

# Override when needed
agent = Agent("assistant", mode="fast")  # Speed-critical apps
agent = Agent("assistant", mode="deep")  # Analysis-heavy tasks
```

### Depth Configuration
```python
agent = Agent("assistant", max_iterations=10)  # Production: balance
agent = Agent("assistant", max_iterations=5, mode="fast")  # Development
agent = Agent("assistant", max_iterations=25, mode="deep")  # Research
```

### Memory Integration
```python
agent = Agent("assistant", memory=True)
# Remembers context for better reasoning
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
agent.run("Research renewable energy trends and create report")
# Deep analysis with multiple passes
```

### Chat Bot
```python
agent = Agent("chatbot", mode="fast", max_iterations=3)
agent.run("Hello, how are you?")
# Quick, friendly response
```

### Code Assistant
```python
agent = Agent("coder", mode="adapt")
agent.run("Fix this bug: [code snippet]")
# Auto-chooses depth based on complexity
```

---

*Adaptive reasoning for Cogency v1.2.2*