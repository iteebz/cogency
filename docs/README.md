# Cogency Documentation

**Smart AI agents that think as hard as they need to.**

Cogency provides production-ready AI agents with adaptive reasoning, built-in tools, and persistent memory.

## Quick Links

- **[Quick Start](quickstart.md)** - Get running in 5 minutes
- **[API Reference](api.md)** - Complete Agent class documentation
- **[Tools](tools.md)** - Built-in tools and custom tool creation
- **[Examples](examples.md)** - Detailed code examples and walkthroughs

## Core Features

- **Adaptive Reasoning** - Automatically switches between fast and deep thinking modes
- **Built-in Tools** - Files, shell, HTTP, scrape, search
- **Situated Memory** - Learns about users and provides contextual understanding
- **Streaming Execution** - Watch agents think in real-time
- **Zero Configuration** - Auto-detects LLM providers and sensible defaults

## Installation

```bash
pip install cogency
```

Set your LLM API key:
```bash
export OPENAI_API_KEY=sk-...
# or ANTHROPIC_API_KEY, GEMINI_API_KEY, etc.
```

## Basic Usage

```python
from cogency import Agent

agent = Agent("assistant")

# Simple usage
result = agent.run("What's 15% of $1,250?")

# Streaming with real-time feedback
async for chunk in agent.stream("Plan a Tokyo trip with $2000 budget"):
    print(chunk, end="", flush=True)
```

## Documentation Structure

### Getting Started
- **[Quick Start](quickstart.md)** - Installation and first steps
- **[Examples](examples.md)** - Working code examples

### API Reference  
- **[Agent API](api.md)** - Complete constructor and method documentation
- **[Tools](tools.md)** - Built-in tools and custom tool creation
- **[Configuration](config.md)** - Advanced configuration options

### Guides
- **[Memory](memory.md)** - Memory backends and persistence
- **[Reasoning](reasoning.md)** - Understanding adaptive reasoning modes
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions

---

*Cogency v1.0.0 - Production-ready AI agents with adaptive reasoning*