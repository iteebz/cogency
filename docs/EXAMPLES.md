# Examples

## Multi-Step Debugging

```python
from cogency import Agent

agent = Agent(llm="gemini")

# Agent streams thinking and tool usage
result = await agent("""
Debug this Python script and fix any issues:
- Check syntax errors
- Test the fixed version  
- Explain what was wrong
""")
```

**Stream output:**
```
§THINK: I need to read the script first to identify issues
§CALLS: [{"name": "read", "args": {"file": "script.py"}}]
§YIELD:
[SYSTEM: File content shows missing colon on line 15]
§THINK: Found syntax error, let me fix it
§CALLS: [{"name": "edit", "args": {"file": "script.py", "old": "if condition", "new": "if condition:"}}]
§YIELD:
[SYSTEM: File edited successfully]
§RESPOND: Fixed missing colon on line 15. Script should run correctly now.
```

## Custom Tools

```python
from cogency import Agent, Tool
from cogency.core.result import Ok, Err

class GitTool(Tool):
    @property 
    def name(self):
        return "git_status"
        
    @property
    def description(self):
        return "Check git repository status"
        
    async def execute(self, **kwargs):
        import subprocess
        try:
            result = subprocess.run(["git", "status", "--porcelain"], 
                                  capture_output=True, text=True)
            return Ok(f"Git status: {result.stdout}")
        except Exception as e:
            return Err(f"Git error: {e}")

agent = Agent(tools=[GitTool()])
result = await agent("What's the current git status?")
```

## Provider Switching

```python
# Start with fast provider
agent = Agent(llm="gemini")
result = await agent("Quick analysis of this file")

# Switch to more capable provider for complex tasks
agent = Agent(llm="openai")  
result = await agent("Refactor this entire codebase")

# Anthropic for reasoning-heavy tasks
agent = Agent(llm="anthropic")
result = await agent("Explain the philosophical implications")
```

## Conversation Continuity

```python
# Session 1
agent = Agent()
await agent("Start debugging session", user_id="dev", conversation_id="debug_001")

# Session 2 (hours later, fresh agent instance)
agent = Agent()  # No state carried over
result = await agent(
    "Continue where we left off", 
    user_id="dev", 
    conversation_id="debug_001"  # Context loaded from storage
)
# Agent remembers entire debugging history
```

## Error Recovery

```python
try:
    agent = Agent(llm="openai")
    result = await agent("Complex multi-step task")
except RuntimeError as e:
    # Graceful fallback
    agent = Agent(llm="gemini") 
    result = await agent("Same task, different provider")
```

## Performance Comparison

```python
import time

# HTTP mode (traditional)
start = time.time()
agent = Agent(mode="replay")
result = await agent("Multi-step file analysis")
http_time = time.time() - start

# WebSocket mode (bidirectional)  
start = time.time()
agent = Agent(mode="resume")
result = await agent("Multi-step file analysis")
ws_time = time.time() - start

print(f"HTTP: {http_time:.2f}s, WebSocket: {ws_time:.2f}s")
```