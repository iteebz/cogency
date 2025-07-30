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
from cogency import Robust
agent = Agent(robust=Robust(rate_limit_rps=1.0, attempts=5))
```

## Common Issues

**Timeouts:**
```python
agent = Agent(robust=Robust(timeout=120.0), depth=5, mode="fast")
```

**Tool failures:**
```python
agent = Agent(debug=True)  # See detailed errors
```

**Memory issues:**
```python
agent = Agent()  # Uses .cogency/memory by default
agent = Agent(memory=None)  # Disable if not needed
```

**JSON parsing:**
```python
agent = Agent(debug=True, mode="fast", depth=3)
```

## Performance

**Speed up:**
```python
agent = Agent(
    mode="fast",
    depth=3,
    notify=False,
    observe=False,
    persist=False
)
```

**Reduce memory:**
```python
agent = Agent(memory=None, depth=5)
agent.user_states.clear()  # Clear periodically
```

**Token limits:**
```python
agent = Agent(mode="fast", depth=3)
agent.user_states.clear()  # Reset context
```

## Debugging

```python
# Debug mode
agent = Agent(debug=True)
result = await agent.run("Your query")
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
agent = Agent(depth=5, mode="fast", debug=True)
```

**Tool selection:**
```python
from cogency.tools import get_tools, Calculator
print([tool.name for tool in get_tools()])
agent = Agent(tools=[Calculator()])  # Explicit tools
```

**Context loss:**
```python
# Use consistent user_id
await agent.run("Remember: I like Python", user_id="alice")
await agent.run("What do I like?", user_id="alice")
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
agent = Agent(persist=False, notify=False)

def lambda_handler(event, context):
    return {'response': await agent.run(event['query'])}
```

## Debug Info

```python
# Minimal reproduction
from cogency import Agent
import logging

logging.basicConfig(level=logging.DEBUG)
agent = Agent(debug=True)

try:
    result = await agent.run("Your failing query")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
```