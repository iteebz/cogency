# Troubleshooting

Common issues and solutions for Cogency agents.

## Installation Issues

### Package Not Found
```bash
pip install cogency
```

If installation fails:
```bash
# Update pip first
pip install --upgrade pip

# Install with verbose output
pip install -v cogency

# Install from source
pip install git+https://github.com/your-org/cogency.git
```

### Dependency Conflicts
```bash
# Create clean virtual environment
python -m venv cogency-env
source cogency-env/bin/activate  # Linux/Mac
# or
cogency-env\Scripts\activate     # Windows

pip install cogency
```

## API Key Issues

### No API Key Configured
```
Error: No LLM provider configured. Set OPENAI_API_KEY, ANTHROPIC_API_KEY, or other supported provider.
```

**Solution:**
```bash
# Set environment variable
export OPENAI_API_KEY=sk-your-key-here

# Or create .env file
echo "OPENAI_API_KEY=sk-your-key-here" > .env
```

### Invalid API Key
```
Error: Authentication failed. Please check your API key.
```

**Solutions:**
1. Verify API key is correct
2. Check API key has proper permissions
3. Ensure API key hasn't expired
4. Try a different LLM provider

### Rate Limiting
```
Error: Rate limit exceeded. Please try again later.
```

**Solutions:**
```python
from cogency import Robust

# Reduce rate limiting
agent = Agent(robust=Robust(rate_limit_rps=1.0))

# Add retry with backoff
agent = Agent(robust=Robust(
    attempts=5,
    backoff="exponential",
    backoff_max=60.0
))
```

## Runtime Errors

### Agent Execution Timeout
```
Error: Agent execution timed out after 60 seconds
```

**Solutions:**
```python
# Increase timeout
agent = Agent(robust=Robust(timeout=120.0))

# Reduce reasoning depth
agent = Agent(depth=5)

# Use fast mode for quicker responses
agent = Agent(mode="fast")
```

### Tool Execution Failures
```
Error: Tool 'search' failed: Connection timeout
```

**Solutions:**
```python
# Enable debug mode to see detailed errors
agent = Agent(debug=True)

# Configure robust retry
agent = Agent(robust=Robust(
    attempts=3,
    timeout=30.0
))

# Check tool-specific configuration
# For search tool, verify internet connection
# For file tools, verify file permissions
```

### Memory Issues
```
Error: Memory backend not available
```

**Solutions:**
```python
# Use default filesystem memory
agent = Agent()  # Uses .cogency/memory by default

# Specify custom memory directory
agent = Agent(memory_dir="./custom_memory")

# Disable memory if not needed
agent = Agent(memory=None)
```

### JSON Parsing Errors
```
Error: Failed to parse LLM response as JSON
```

**Solutions:**
```python
# Enable debug mode to see raw responses
agent = Agent(debug=True)

# Try different LLM provider
agent = Agent(llm=AnthropicLLM())  # Instead of OpenAI

# Reduce complexity to avoid malformed responses
agent = Agent(mode="fast", depth=3)
```

## Performance Issues

### Slow Response Times
```python
# Profile execution time
import time

start = time.time()
result = await agent.run("Your query")
print(f"Execution time: {time.time() - start:.2f}s")
```

**Solutions:**
```python
# Use fast mode
agent = Agent(mode="fast")

# Reduce reasoning depth
agent = Agent(depth=3)

# Disable unnecessary features
agent = Agent(
    notify=False,    # Disable progress notifications
    debug=False,     # Disable debug tracing
    observe=False,   # Disable telemetry
    persist=False    # Disable state persistence
)

# Optimize tool selection
from cogency.tools import Calculator, Search
agent = Agent(tools=[Calculator(), Search()])  # Only needed tools
```

### High Memory Usage
```python
# Monitor memory usage
import psutil
import os

process = psutil.Process(os.getpid())
print(f"Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB")
```

**Solutions:**
```python
# Limit conversation history
agent = Agent(depth=5)

# Use lightweight memory backend
agent = Agent(memory=None)  # Disable memory

# Clear agent state periodically
agent.user_states.clear()
```

### Token Limit Exceeded
```
Error: Request exceeds maximum token limit
```

**Solutions:**
```python
# Reduce reasoning depth
agent = Agent(depth=3)

# Use fast mode to minimize context
agent = Agent(mode="fast")

# Clear conversation history
agent.user_states.clear()

# Use a model with higher token limits
agent = Agent(llm=OpenAILLM(model="gpt-4-turbo"))
```

## Debugging Techniques

### Enable Debug Mode
```python
agent = Agent(debug=True)
result = await agent.run("Your query")

# View execution traces
traces = agent.traces()
for trace in traces:
    print(f"Phase: {trace.get('phase', 'unknown')}")
    print(f"Message: {trace.get('message', 'no message')}")
    print("---")
```

### Stream Execution
```python
# Watch agent thinking in real-time
async for chunk in agent.stream("Complex query"):
    print(chunk, end="", flush=True)
```

### Custom Logging
```python
import logging

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("cogency")

# Custom callback for notifications
async def log_callback(message):
    logger.info(f"Agent: {message}")

agent = Agent(callback=log_callback)
```

### Tool-Specific Debugging
```python
# Debug specific tools
from cogency.tools import Calculator

calc = Calculator()
result = await calc.run("2 + 2")
print(f"Calculator result: {result}")

# Test tool schema
print(f"Schema: {calc.get_schema()}")
print(f"Examples: {calc.get_usage_examples()}")
```

## Common Error Patterns

### Infinite Loops
```
Agent stuck in reasoning loop, exceeding depth limit
```

**Solutions:**
```python
# Reduce depth limit
agent = Agent(depth=5)

# Use fast mode to prevent complex loops
agent = Agent(mode="fast")

# Enable debug to see loop patterns
agent = Agent(debug=True)
```

### Tool Selection Issues
```
Agent not using expected tools
```

**Solutions:**
```python
# Verify tools are available
from cogency.tools import get_tools
print([tool.name for tool in get_tools()])

# Specify tools explicitly
from cogency.tools import Calculator, Search
agent = Agent(tools=[Calculator(), Search()])

# Check tool descriptions
for tool in get_tools():
    print(f"{tool.name}: {tool.description}")
```

### Context Loss
```
Agent forgetting previous conversation context
```

**Solutions:**
```python
# Enable memory
agent = Agent()  # Memory enabled by default

# Use same user_id for conversation continuity
await agent.run("Remember I like Python", user_id="user123")
await agent.run("What language do I like?", user_id="user123")

# Enable state persistence
agent = Agent(persist=True)
```

## Environment-Specific Issues

### Docker Deployment
```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Set environment variables
ENV OPENAI_API_KEY=your-key-here
ENV COGENCY_MEMORY_DIR=/app/memory

CMD ["python", "app.py"]
```

### Kubernetes Deployment
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cogency-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: cogency-agent
  template:
    metadata:
      labels:
        app: cogency-agent
    spec:
      containers:
      - name: cogency-agent
        image: your-registry/cogency-agent:latest
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: openai-key
        - name: COGENCY_MEMORY_DIR
          value: "/app/memory"
        volumeMounts:
        - name: memory-storage
          mountPath: /app/memory
      volumes:
      - name: memory-storage
        persistentVolumeClaim:
          claimName: cogency-memory-pvc
```

### AWS Lambda
```python
# lambda_function.py
import json
from cogency import Agent

# Initialize agent outside handler for reuse
agent = Agent("lambda-agent", 
              persist=False,  # Lambda is stateless
              notify=False)   # Clean logs

def lambda_handler(event, context):
    try:
        query = event.get('query', '')
        result = await agent.run(query)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'response': result})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

## Getting Help

### Enable Verbose Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

agent = Agent(debug=True, notify=True)
```

### Collect Debug Information
```python
# System information
import sys
import platform
print(f"Python: {sys.version}")
print(f"Platform: {platform.platform()}")

# Cogency version
import cogency
print(f"Cogency: {cogency.__version__}")

# Configuration
agent = Agent(debug=True)
print(f"LLM: {type(agent.llm).__name__}")
print(f"Tools: {[tool.name for tool in agent.tools]}")
print(f"Memory: {type(agent.memory).__name__}")
```

### Minimal Reproduction
```python
# Create minimal example that reproduces the issue
from cogency import Agent

agent = Agent(debug=True)
try:
    result = await agent.run("Simple query that fails")
    print(result)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
```

---

*For additional help, check the GitHub issues or create a new issue with debug information.*