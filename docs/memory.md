# Memory

**Smart memory that learns about users without external dependencies.**

```python
from cogency import Agent

# Enable memory with one parameter
agent = Agent("assistant", memory=True)

# Memory learns automatically
await agent.run("I prefer TypeScript over JavaScript")
await agent.run("What language should I use for my project?")
# → Agent recalls your TypeScript preference
```

## How It Works

Memory uses a two-layer architecture:

1. **Recent interactions** - Raw conversation history with human/agent weighting
2. **User impression** - LLM-synthesized understanding of the user

When recent interactions exceed 16K tokens, the LLM automatically synthesizes them into a refined user impression, preserving essential context while eliminating noise.

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
await agent.run("I work primarily with Python and React")
await agent.run("I prefer functional programming patterns")
await agent.run("Help me design an API")
# → Agent uses your preferences to guide design recommendations
```

## Memory API

The memory system provides two core methods:

### `remember(content, human=False)`
Store information with optional human weighting:

```python
# Direct memory access (rarely needed)
await agent.memory.remember("User prefers minimal APIs", human=True)
await agent.memory.remember("Agent suggested REST approach", human=False)
```

### `recall()`
Retrieve memory context for reasoning:

```python
context = await agent.memory.recall()
# Returns formatted context:
# USER IMPRESSION:
# [Synthesized understanding]
# 
# RECENT INTERACTIONS: 
# [HUMAN] Recent user input
# [AGENT] Recent agent response
```

## Persistence

Memory automatically persists across sessions when combined with the `persist` option:

```python
agent = Agent("assistant", memory=True, persist=True)

# First session
await agent.run("I'm working on a React app")

# Later session (different process)
agent = Agent("assistant", memory=True, persist=True)  
await agent.run("Continue helping with my project")
# → Agent remembers it's a React app
```

## Memory Synthesis

When recent interactions grow large (>16K tokens), memory automatically synthesizes:

```python
# Before synthesis - detailed interactions
RECENT INTERACTIONS:
[HUMAN] I prefer TypeScript over JavaScript  
[AGENT] TypeScript provides better type safety
[HUMAN] I like functional programming
[AGENT] Consider using immutable data structures
# ... many more interactions ...

# After synthesis - refined impression  
USER IMPRESSION:
Developer with strong preferences for TypeScript and functional programming patterns. 
Values type safety and immutable data structures. Working on React applications.
```

## Best Practices

**Let memory work automatically** - The system learns from natural conversation without manual intervention.

**Trust human priority** - User statements automatically override agent observations during synthesis.

**Enable persistence for continuity** - Combine `memory=True` with `persist=True` for cross-session learning.

```python
# Recommended setup for persistent learning
agent = Agent(
    "assistant", 
    memory=True,
    persist=True
)
```

## Memory vs Workspace

- **Memory**: Persistent user context (preferences, identity, long-term facts)
- **Workspace**: Ephemeral task context (current objective, discoveries, approach)

Memory learns *about* the user. Workspace tracks *current* reasoning state.

## Advanced Configuration

```python
from cogency.config import MemoryConfig

config = MemoryConfig(
    synthesis_threshold=8000,  # Trigger synthesis earlier
    user_id="specific_user"    # Multi-user memory isolation
)

agent = Agent("assistant", memory=config)
```

## Technical Details

Memory is implemented as pure LLM reasoning without vector databases or embeddings:

- **Direct Context Injection** - Memory embedded directly in reasoning prompts
- **LLM Attention Filtering** - Natural relevance determination during reasoning  
- **Synthesis-based Compression** - LLM-driven compression preserves meaning
- **Zero External Dependencies** - No additional infrastructure required

This approach eliminates retrieval latency and provides natural relevance filtering through LLM attention mechanisms.