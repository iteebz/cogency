# Cogency (Python)

> **Multi-step reasoning agents with clean DX**

## Installation

```bash
pip install cogency
```

## Quick Start

```python
from cogency.agent import Agent
from cogency.llm import GeminiLLM, KeyRotator
from cogency.tools.calculator import CalculatorTool

# Setup LLM with key rotation
keys = ["key1", "key2", "key3"]
key_rotator = KeyRotator(keys)
llm = GeminiLLM(key_rotator=key_rotator)

# Create agent with tools
agent = Agent(
    name="MathAgent", 
    llm=llm, 
    tools=[CalculatorTool()]
)

# Run with tracing
result = agent.run("What is 15 * 23?", enable_trace=True)
print("Response:", result["response"])
```

## Core Architecture

Cogency uses a clean 5-step reasoning loop:

1. **Plan** - Decide strategy and if tools are needed
2. **Reason** - Select tools and prepare inputs
3. **Act** - Execute tools with validation
4. **Reflect** - Evaluate results and decide next steps
5. **Respond** - Format clean answer for user

## Built-in Tools

Tools are auto-discovered from the `/tools/` directory:

- `CalculatorTool` - Basic arithmetic operations
- `WebSearchTool` - Web search using DuckDuckGo

## Adding Custom Tools

Create a new tool by extending the `BaseTool` base class:

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

Drop the file in `/tools/` and it's automatically available.

## LLM Support

### Gemini
```python
from cogency.llm import GeminiLLM

llm = GeminiLLM(api_key="your-key")
# or with key rotation
llm = GeminiLLM(key_rotator=KeyRotator(["key1", "key2"]))
```

### OpenAI (coming soon)
```python
from cogency.llm import OpenAILLM

llm = OpenAILLM(api_key="your-key")
```

## Tracing

Enable detailed execution tracing to debug your agents:

```python
result = agent.run("Complex task", enable_trace=True)

if "execution_trace" in result:
    from cogency.utils.formatting import format_trace
    print(format_trace(result["execution_trace"]))
```

Example trace output:
```
--- Execution Trace (ID: abc123) ---
PLAN     | Need to calculate complex math problem
REASON   | TOOL_CALL: calculator(operation='multiply', num1=15, num2=23)
ACT      | calculator -> {'result': 345}
REFLECT  | Calculation completed successfully
RESPOND  | 15 multiplied by 23 equals 345.
--- End Trace ---
```

## Error Handling

All tools include built-in validation and error handling:

```python
# Invalid tool calls are caught and reported
result = agent.run("Calculate abc + def")
# Returns clean error message instead of crashing
```

## CLI Usage

Run the example from command line:

```bash
cd python
poetry run python ../examples/basic_usage.py
```

## Configuration

Agents are configured through simple constructor parameters:

```python
agent = Agent(
    name="MyAgent",           # Agent identifier
    llm=llm,                 # LLM instance
    tools=[tool1, tool2],    # List of available tools
    max_iterations=10        # Optional: limit reasoning loops
)
```

## Development

### Running Tests
```bash
poetry run pytest
```

### Adding New LLMs
Extend the `BaseLLM` class and implement required methods:

```python
from cogency.llm import GeminiLLM

class YourLLM(GeminiLLM):
    def generate(self, prompt: str, **kwargs) -> str:
        # Your implementation
        pass
```

## Roadmap

- ✅ Multi-step reasoning loop
- ✅ Tool auto-discovery
- ✅ Clean execution tracing
- ✅ Error handling and validation
- 🔄 OpenAI + Anthropic LLM support
- 🔄 Memory and persistence
- 🔄 Multi-agent coordination
- 🔄 Streaming responses

## License

MIT License - see [LICENSE](../LICENSE) for details.