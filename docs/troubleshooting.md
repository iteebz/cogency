# Troubleshooting

## Installation

```bash
pip install cogency

# If problems:
pip install --upgrade pip
pip install -v cogency
```

## API Keys

```bash
# Set any supported provider
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
export GEMINI_API_KEY=...

# Or .env file
echo "OPENAI_API_KEY=sk-..." > .env
```

**Rate limits:**
```python
from cogency import Agent, RobustConfig
# Simple: enable with defaults
agent = Agent("assistant", robust=True)
# Advanced: custom settings
agent = Agent("assistant", robust=RobustConfig(rate_limit_rps=1.0, attempts=5))
```

## Common Issues

**Timeouts:**
```python
# Simple: enable robustness with defaults
agent = Agent("assistant", robust=True, max_iterations=5)
# Advanced: custom timeout
agent = Agent("assistant", robust=RobustConfig(timeout=120.0), max_iterations=5)
```

**Tool failures:**
```python
agent = Agent(debug=True)  # See detailed errors
```

**Memory issues:**
```python
agent = Agent(memory=True)  # Uses .cogency/memory by default
agent = Agent(memory=False)  # Disable if not needed
```

**JSON parsing:**
```python
agent = Agent(debug=True, max_iterations=3)
```

## Performance

**Speed up:**
```python
agent = Agent(
    mode="fast",
    max_iterations=3,
    notify=False,
    memory=False
)
```

**Reduce memory:**
```python
agent = Agent(memory=False, max_iterations=5)
# Clear user states periodically if needed
```

**Token limits:**
```python
agent = Agent(max_iterations=3)
# Agent automatically manages context
```

## Debugging

```python
# Debug mode
agent = Agent(debug=True)
result = agent.run("Your query")
traces = agent.traces()  # Detailed execution steps

# Stream execution
async for chunk in agent.stream("Complex query"):
    print(chunk, end="", flush=True)

# Custom logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Common Patterns

**Infinite loops:**
```python
agent = Agent(max_iterations=5, debug=True)
```

**Tool selection:**
```python
agent = Agent(tools=["files", "shell"])  # Explicit tools
```

**Context consistency:**
```python
# Use consistent user_id
agent.run("Remember: I like Python", user_id="alice")
agent.run("What do I like?", user_id="alice")
```

## Production

**Docker:**
```dockerfile
FROM python:3.10-slim
RUN pip install cogency
ENV OPENAI_API_KEY=sk-...
CMD ["python", "app.py"]
```

**Lambda:**
```python
from cogency import Agent
agent = Agent(memory=False, notify=False)

def lambda_handler(event, context):
    return {'response': agent.run(event['query'])}
```

## Debug Info

```python
# Minimal reproduction
from cogency import Agent
import logging

logging.basicConfig(level=logging.DEBUG)
agent = Agent(debug=True)

try:
    result = agent.run("Your failing query")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
```

## Error Messages

**"No LLM provider found"**
- Set an API key: `export OPENAI_API_KEY=sk-...`

**"Tool not found"**
- Check tool name: `agent = Agent(tools=["files", "shell"])`

**"Memory synthesis failed"**
- Reduce memory load: `agent = Agent(memory=False)`

**"Timeout error"**
- Increase timeout: `agent = Agent(robust=RobustConfig(timeout=300.0))`

**"Rate limit exceeded"**
- Add rate limiting: `agent = Agent(robust=RobustConfig(rate_limit_rps=1.0))`

---

*Production troubleshooting for Cogency v1.0.0*