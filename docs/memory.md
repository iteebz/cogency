# Memory

**Situated memory that learns about users and provides contextual understanding.**

```python
from cogency import Agent

# Enable memory with one parameter  
agent = Agent("assistant", memory=True)

# Memory learns automatically
agent.run("I prefer TypeScript over JavaScript")
agent.run("What language should I use for my project?")
# → Agent recalls your TypeScript preference and provides situated context
```

## How It Works

Memory uses **situated memory architecture** - persistent user understanding that builds over time:

1. **User Profile** - Persistent understanding of preferences, goals, expertise, and patterns
2. **LLM Synthesis** - Automatic profile updates through intelligent interaction analysis  
3. **Context Injection** - Seamless integration into agent reasoning

The system automatically learns from interactions and synthesizes understanding without external dependencies.

## Key Features

- **Zero configuration** - Just set `memory=True`
- **No external dependencies** - Pure LLM-based architecture  
- **Human priority** - User statements override agent observations
- **Automatic synthesis** - Compresses interactions intelligently
- **Cross-session persistence** - Remembers between conversations

## Basic Usage

```python
# Simple memory activation
agent = Agent("assistant", memory=True)

# Memory learns from every interaction
agent.run("I work primarily with Python and React")
agent.run("I prefer functional programming patterns")
agent.run("Help me design an API")
# → Agent uses your preferences to guide design recommendations
```

## Memory API

Memory works automatically through agent interactions. The system tracks:

- **Preferences** - Language choices, communication style, technical preferences
- **Goals** - Current objectives and long-term aspirations  
- **Expertise** - Technical knowledge areas and skill levels
- **Projects** - Active work and context
- **Patterns** - What works and what doesn't for the user

```python
# Memory learns from natural conversation
agent.run("I prefer functional programming patterns")
agent.run("I'm working on a React app with TypeScript")
agent.run("Help me design a clean API")
# → Agent uses your preferences and project context automatically
```

## Persistence

Memory automatically persists across sessions:

```python
agent = Agent("assistant", memory=True)

# First session
agent.run("I'm working on a React app")

# Later session (different process)
agent = Agent("assistant", memory=True)  
agent.run("Continue helping with my project")
# → Agent remembers it's a React app
```

## Memory Synthesis

Memory automatically refines understanding over time through LLM-driven synthesis:

```python
# Initial interactions build understanding
agent.run("I prefer TypeScript over JavaScript")
agent.run("I like functional programming")  
agent.run("I'm working on a React project")

# After several interactions, memory synthesizes
# Consolidated understanding: 
# "Developer with TypeScript preference, functional programming style, 
#  working on React applications with emphasis on type safety"
```

## Best Practices

**Let memory work automatically** - The system learns from natural conversation without manual intervention.

**Trust human priority** - User statements automatically override agent observations during synthesis.

**Enable memory for continuity** - Use `memory=True` for cross-session learning.

```python
# Recommended setup for persistent learning
agent = Agent(
    "assistant", 
    memory=True
)
```

## Memory vs Reasoning State

- **Memory**: Persistent user understanding (preferences, goals, expertise, patterns)
- **Reasoning**: Ephemeral task context (current objective, strategy, insights)

Memory learns *about* the user across sessions. Reasoning tracks *current* task progress.

## Advanced Configuration

```python
# Memory is enabled by default with memory=True
agent = Agent("assistant", memory=True)

# Custom memory setup with explicit dependencies
from cogency.memory import SituatedMemory
from cogency.providers import OpenAI

memory = SituatedMemory(provider=OpenAI(), store=my_store)
agent = Agent("assistant", memory=memory)
```

## Technical Details

Memory is implemented as pure LLM reasoning without vector databases or embeddings:

- **Direct Context Injection** - Memory embedded directly in reasoning prompts
- **LLM Attention Filtering** - Natural relevance determination during reasoning  
- **Synthesis-based Compression** - LLM-driven compression preserves meaning
- **Zero External Dependencies** - No additional infrastructure required

This approach eliminates retrieval latency and provides natural relevance filtering through LLM attention mechanisms.