# Memory Backends

Agents remember conversations and learn from interactions. You can use the built-in filesystem backend or create custom ones.

## Built-in Filesystem Backend

```python
from cogency import Agent

# Uses .cogency/memory by default
agent = Agent("assistant")

# Custom memory directory
agent = Agent("assistant", memory_dir="./my_memory")
```

## Custom Memory Backend

```python
from cogency.memory import Store
from cogency import Agent

class MyMemory(Store):
    async def save(self, content: str, metadata: dict = None):
        # Your storage logic (database, cloud, etc.)
        print(f"Saving: {content}")
    
    async def search(self, query: str, limit: int = 5) -> list:
        # Your search logic
        # Return list of {"content": str, "metadata": dict} items
        return [
            {"content": "Relevant memory", "metadata": {"timestamp": "2024-01-01"}}
        ]
    
    async def clear(self):
        # Optional: clear all memories
        pass

# Use your custom backend
agent = Agent("assistant", memory=MyMemory())
```

## Memory Operations

Agents automatically save important information and recall it when relevant:

```python
# This conversation will be remembered
from cogency.stream import stream_print
await stream_print(agent.stream("My favorite color is blue"))

# Later, the agent will recall this when relevant
await stream_print(agent.stream("What's my favorite color?"))
# Agent remembers: "Your favorite color is blue"
```

## Memory Metadata

You can include metadata when saving memories:

```python
class TaggedMemory(Store):
    async def save(self, content: str, metadata: dict = None):
        # Add custom metadata
        metadata = metadata or {}
        metadata["tags"] = ["important", "user_preference"]
        # Save with metadata...
```