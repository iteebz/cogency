# Agent Configuration

Complete reference for configuring your agents.

## Basic Configuration

```python
from cogency import Agent

agent = Agent(
    "assistant",                          # Agent name
    personality="helpful coding assistant", # System prompt personality
    tone="professional",                   # Response tone
    style="concise",                      # Response style
    tools=[MyTool(), AnotherTool()],      # Custom tools
    memory=MyMemory(),                    # Custom memory backend
    memory_dir=".my_memory",              # Memory directory (if using default backend)
    llm=MyLLM(),                         # Custom LLM
    trace=True,                          # Enable debug tracing
    enable_mcp=True                      # Enable MCP server
)
```

## Response Shaping

Fine-tune how your agent responds:

```python
response_shaper = {
    "personality": "You are a senior software engineer",
    "tone": "friendly but professional", 
    "style": "concise and practical",
    "constraints": [
        "Always provide code examples",
        "Explain your reasoning",
        "Ask clarifying questions when needed"
    ]
}

agent = Agent("coding_assistant", response_shaper=response_shaper)
```

## System Prompt Override

For complete control over the system prompt:

```python
custom_prompt = """
You are an expert Python developer with 10 years of experience.
You write clean, efficient code and explain complex concepts simply.
Always provide working code examples and test cases.
"""

agent = Agent("expert", system_prompt=custom_prompt)
```

## Tool Selection

```python
from cogency.tools import Calculator, Weather, Search

# Specific tools only
agent = Agent("assistant", tools=[Calculator(), Weather()])

# All available tools (default)
agent = Agent("assistant")  # Auto-discovers all registered tools

# No tools
agent = Agent("assistant", tools=[])
```

## Multi-User Support

```python
# Different users get separate contexts and memory
await agent.query("Remember I like Python", user_id="alice")
await agent.query("Remember I like JavaScript", user_id="bob")

# Each user's preferences are kept separate
await agent.query("What do I like?", user_id="alice")  # "You like Python"
await agent.query("What do I like?", user_id="bob")    # "You like JavaScript"
```