# Cogency (Python)

> **Multi-step reasoning agents with clean architecture**

## Installation

```bash
pip install cogency
```

## Quick Start

```python
from cogency.agent import Agent
from cogency.llm import GeminiLLM
from cogency.tools import CalculatorTool, WebSearchTool, FileManagerTool

# Create agent with multiple tools
llm = GeminiLLM(api_key="your-key")
agent = Agent(
    name="MyAgent", 
    llm=llm, 
    tools=[
        CalculatorTool(), 
        WebSearchTool(), 
        FileManagerTool()
    ]
)

# Execute with tracing
result = agent.run("What is 15 * 23?", enable_trace=True, print_trace=True)
print(result["response"])
```

## Core Architecture

Cogency uses a clean 5-step reasoning loop:

1. **Plan** - Decide strategy and if tools are needed
2. **Reason** - Select tools and prepare inputs
3. **Act** - Execute tools with validation
4. **Reflect** - Evaluate results and decide next steps
5. **Respond** - Format clean answer for user

This separation enables emergent reasoning behavior - agents adapt their tool usage based on results without explicit programming.

## Built-in Tools

- **CalculatorTool** - Basic arithmetic operations
- **WebSearchTool** - Web search using DuckDuckGo
- **FileManagerTool** - File system operations

## Adding Custom Tools

Create a new tool by extending the `BaseTool` class:

```python
from cogency.tools.base import BaseTool

class WeatherTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="weather",
            description="Get current weather for a location"
        )
    
    def run(self, location: str) -> dict:
        # Your implementation here
        return {"temperature": 72, "condition": "sunny"}
```

Tools are automatically discovered and available to agents.

## LLM Support

Currently supports Google Gemini:

```python
from cogency.llm import GeminiLLM

# Simple usage
llm = GeminiLLM(api_key="your-key")

# With key rotation
from cogency.llm import KeyRotator
keys = ["key1", "key2", "key3"]
llm = GeminiLLM(key_rotator=KeyRotator(keys))
```

## Execution Tracing

Enable detailed tracing to see your agent's reasoning:

```python
# Simple trace viewing
result = agent.run("Complex task", enable_trace=True, print_trace=True)

# Or capture trace data
result = agent.run("Complex task", enable_trace=True)
trace_data = result["execution_trace"]
```

Example trace output:
```
--- Execution Trace (ID: abc123) ---
PLAN     | Need to calculate and then search for information
REASON   | TOOL_CALL: calculator(operation='multiply', num1=15, num2=23)
ACT      | calculator -> {'result': 345}
REFLECT  | Calculation completed, now need to search
REASON   | TOOL_CALL: web_search(query='AI developments 2025')
ACT      | web_search -> {'results': [...]}
REFLECT  | Found relevant search results
RESPOND  | 15 multiplied by 23 equals 345. Recent AI developments include...
--- End Trace ---
```

## Error Handling

All tools include built-in validation and graceful error handling:

```python
# Invalid operations are caught and handled
result = agent.run("Calculate abc + def")
# Agent will respond with helpful error message instead of crashing
```

## CLI Usage

Run examples from the command line:

```bash
cd python
python examples/basic_usage.py
```

## Development

### Running Tests
```bash
pytest
```

### Project Structure
```
cogency/
├── agent.py          # Core agent implementation
├── llm/              # LLM integrations
├── tools/            # Built-in tools
├── utils/            # Utilities and formatting
└── tests/            # Test suite (115+ tests)
```

## Emergent Behavior

The key insight behind Cogency is that clean architectural separation enables emergent reasoning. When agents fail with one tool, they automatically reflect and try different approaches:

```python
# Agent fails with poor search query, reflects, and tries again
result = agent.run("Tell me about recent AI developments")

# Trace shows:
# 1. Initial search with generic query
# 2. Poor results returned
# 3. Agent reflects on failure
# 4. Adapts query strategy
# 5. Succeeds with better results
```

This behavior emerges from the Plan → Reason → Act → Reflect → Respond loop, not from explicit programming.

## License

MIT License - see [LICENSE](../LICENSE) for details.