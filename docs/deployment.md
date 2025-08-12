# Deployment

Production deployment for Cogency agents.

## Installation

### Install

```bash
pip install cogency
# Or: pip install cogency[anthropic,openai]
```

### API Keys

**Environment Variables:**
```bash
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
export GEMINI_API_KEY=...
export MISTRAL_API_KEY=... 
export GROQ_API_KEY=gsk_...
```

**`.env` File:**
```bash
# .env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

## Production

### Basic Setup

```python
from cogency import Agent

agent = Agent(
    "production_assistant",
    memory=True,           # Persistent memory
    max_iterations=10,     # Reasonable limits
    notify=False          # Disable notifications
)
```

### Advanced

```python
from cogency import Agent, devops_tools
from cogency.providers import OpenAI, Anthropic

agent = Agent(
    "production_agent",
    memory=True,
    tools=devops_tools(),
    providers=[
        OpenAI(api_key="sk-..."),        # Primary
        Anthropic(api_key="sk-ant-...")  # Fallback
    ],
    max_iterations=15,
    handlers=[custom_logging_handler]
)
```

## Error Handling

### Built-in Resilience

Automatic error handling:

- **API failures**: Auto-retry with backoff
- **Tool failures**: Graceful degradation, continues
- **Memory failures**: Continues without memory if needed
- **Rate limiting**: Built-in retry

### Custom Handling

```python
try:
    result = agent.run("Deploy application")
    if not result:
        logger.error("Agent returned empty result")
except Exception as e:
    logger.error(f"Agent execution failed: {e}")
    # Fallback logic
```

## Observability

### Logging

```python
agent = Agent("assistant", debug=True)  # Detailed logging
result = agent.run("Task")

# Access logs
logs = agent.logs()
for log in logs:
    print(f"{log.get('type')}: {log.get('content')}")
```

### Event Handling

```python
def production_handler(event):
    if event.get('type') == 'error':
        monitoring.alert(event)  # Send to monitoring
    elif event.get('type') == 'tool':
        logger.info(f"Tool used: {event.get('name')}")  # Log usage

agent = Agent("assistant", handlers=[production_handler])
```

## Security

### Input Validation

Built-in semantic security:

```python
result = agent.run("rm -rf /")  # ❌ Blocked
result = agent.run("List directory contents")  # ✅ Allowed
```

### API Key Security

**Best Practices:**
- Environment variables, never hardcode
- Rotate keys regularly  
- Separate dev/production keys
- Monitor for anomalies

## Performance

### Async Usage

```python
import asyncio

async def main():
    agent = Agent("assistant")
    
    tasks = [
        agent.run_async("Task 1"),
        agent.run_async("Task 2"), 
        agent.run_async("Task 3")
    ]
    
    return await asyncio.gather(*tasks)

results = asyncio.run(main())
```

### Resource Limits

```python
agent = Agent(
    "assistant",
    max_iterations=10,     # Prevent loops
    memory=True,          # Efficient memory
    notify=False          # Reduce overhead
)
```

## Monitoring

### Health Checks

```python
def health_check():
    try:
        agent = Agent("health_check")
        result = agent.run("What's 2+2?")
        return "healthy" if result and "4" in result else "unhealthy"
    except Exception:
        return "unhealthy"
```

### Usage Tracking

```python
class UsageHandler:
    def __init__(self):
        self.usage_stats = {}
    
    def __call__(self, event):
        event_type = event.get('type')
        self.usage_stats[event_type] = self.usage_stats.get(event_type, 0) + 1

usage_handler = UsageHandler()
agent = Agent("assistant", handlers=[usage_handler])
```

## Container Deployment

### Docker

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . .

# Set environment
ENV PYTHONPATH=/app
ENV OPENAI_API_KEY=${OPENAI_API_KEY}

CMD ["python", "main.py"]
```

### requirements.txt
```
cogency>=1.2.2
```

## Cloud Deployment

### Environment Setup

**AWS/GCP/Azure:**
```bash
# Secrets manager
export OPENAI_API_KEY=$(aws secretsmanager get-secret-value --secret-id openai-key --query SecretString --output text)

# Cloud provider services
export OPENAI_API_KEY=${AWS_OPENAI_KEY}
```

**Kubernetes:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: cogency-keys
data:
  openai-key: <base64-encoded-key>
---
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
      - name: agent
        image: your-app:latest
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: cogency-keys
              key: openai-key
```

## Troubleshooting

### Common Issues

**API Key Not Found:**
```python
# Explicit provider configuration
from cogency.providers import OpenAI
agent = Agent("assistant", providers=[OpenAI(api_key="sk-...")])
```

**Memory Issues:**
```python
agent = Agent("assistant", memory=True)  # Auto-reinitializes if corrupted
```

**Tool Failures:**
```python
logs = agent.logs(type='tool', errors_only=True)
for error in logs:
    print(f"Tool error: {error}")
```

## Production Checklist

- [ ] API keys via environment variables
- [ ] Error handling and logging  
- [ ] Resource limits configured
- [ ] Health checks implemented
- [ ] Monitoring and alerting
- [ ] Security validated (no hardcoded secrets)
- [ ] Performance tested
- [ ] Backup/recovery documented

---

*Advanced patterns in [examples](../examples/).*