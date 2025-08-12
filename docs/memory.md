# Memory

**Learns about users and provides contextual understanding.**

```python
from cogency import Agent

agent = Agent("assistant", memory=True)

# Learns automatically
agent.run("I prefer TypeScript over JavaScript")
agent.run("What language should I use for my project?")
# → Recalls preference and provides context
```

## How It Works

Persistent user understanding that builds over time:

1. **User Profile** - Preferences, goals, expertise, patterns
2. **LLM Synthesis** - Auto-updates through interaction analysis  
3. **Context Injection** - Seamless integration into reasoning

Learns from interactions and synthesizes understanding without external dependencies.

## Key Features

- **Zero configuration** - Set `memory=True`
- **No dependencies** - Pure LLM architecture  
- **Human priority** - User statements override observations
- **Auto-synthesis** - Compresses interactions intelligently
- **Cross-session** - Remembers between conversations

## Basic Usage

```python
agent = Agent("assistant", memory=True)

# Learns from every interaction
agent.run("I work primarily with Python and React")
agent.run("I prefer functional programming patterns")
agent.run("Help me design an API")
# → Uses preferences to guide design recommendations
```

## What It Tracks

Works automatically through interactions. Tracks:

- **Preferences** - Language choices, communication style, technical preferences
- **Goals** - Objectives and aspirations  
- **Expertise** - Knowledge areas and skill levels
- **Projects** - Active work and context
- **Patterns** - What works and what doesn't

```python
# Learns from natural conversation
agent.run("I prefer functional programming patterns")
agent.run("I'm working on a React app with TypeScript")
agent.run("Help me design a clean API")
# → Uses preferences and project context automatically
```

## Persistence

Auto-persists across sessions:

```python
agent = Agent("assistant", memory=True)

# First session
agent.run("I'm working on a React app")

# Later session
agent = Agent("assistant", memory=True)  
agent.run("Continue helping with my project")
# → Remembers it's a React app
```

## Synthesis

Auto-refines understanding over time:

```python
# Initial interactions build understanding
agent.run("I prefer TypeScript over JavaScript")
agent.run("I like functional programming")  
agent.run("I'm working on a React project")

# After several interactions, synthesizes:
# "Developer with TypeScript preference, functional programming style, 
#  working on React apps with emphasis on type safety"
```

## Best Practices

**Let memory work automatically** - Learns from natural conversation.

**Trust human priority** - User statements override observations.

**Enable for continuity** - Use `memory=True` for cross-session learning.

```python
agent = Agent("assistant", memory=True)
```

## Memory vs Reasoning

- **Memory**: Persistent user understanding (preferences, goals, expertise)
- **Reasoning**: Ephemeral task context (objective, strategy, insights)

Memory learns *about* the user. Reasoning tracks *current* task progress.

## Advanced

```python
agent = Agent("assistant", memory=True)  # Default

# Custom setup
from cogency.memory import Memory
from cogency.providers import OpenAI

memory = Memory(provider=OpenAI(), store=my_store)
agent = Agent("assistant", memory=memory)
```

## Technical

Pure LLM reasoning without vector databases or embeddings:

- **Direct Context Injection** - Embedded in reasoning prompts
- **LLM Attention Filtering** - Natural relevance determination  
- **Synthesis Compression** - LLM-driven compression preserves meaning
- **Zero Dependencies** - No additional infrastructure

Eliminates retrieval latency and provides natural relevance filtering.