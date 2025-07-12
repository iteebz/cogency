# Cogency (Python)

> **Multi-step reasoning agents with clean architecture**

## Installation

```bash
pip install cogency
```

## Quick Start

### Standard Execution
```python
from cogency.agent import Agent
from cogency.llm import GeminiLLM
from cogency.tools import CalculatorTool, WebSearchTool, FileManagerTool

# Create agent with multiple tools
llm = GeminiLLM(api_keys="your-key")  # New cleaner interface
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
result = await agent.run("What is 15 * 23?", enable_trace=True, print_trace=True)
print(result["response"])
```

### Streaming Execution (NEW in 0.3.0)
```python
# Stream agent execution in real-time - see thinking process as it happens
async for chunk in agent.stream("What is 15 * 23?"):
    if chunk["type"] == "thinking":
        print(f"💭 {chunk['content']}")
    elif chunk["type"] == "chunk":
        print(f"🧠 {chunk['content']}", end="")
    elif chunk["type"] == "result":
        print(f"\n✅ {chunk['node']}: {chunk['data']}")

# Example output:
# 💭 Analyzing user request and available tools...
# 💭 Available tools: calculator (Basic arithmetic operations)
# 💭 Generating plan decision...
# 🧠 {"action": "tool_needed", "reasoning": "Math calculation", "strategy": "calculator"}
# ✅ plan: {"decision": "..."}
# 💭 Analyzing task and selecting appropriate tool...
# 💭 Available tools: ['calculator']
# 🧠 TOOL_CALL: calculator(operation='multiply', x1=15, x2=23)
# ✅ reason: {"tool_call": "..."}
```

## Core Architecture

Cogency uses a clean 5-step reasoning loop:

1. **Plan** - Decide strategy and if tools are needed
2. **Reason** - Select tools and prepare inputs
3. **Act** - Execute tools with validation
4. **Reflect** - Evaluate results and decide next steps
5. **Respond** - Format clean answer for user

This separation enables emergent reasoning behavior - agents adapt their tool usage based on results without explicit programming.

### Stream-First Design (0.3.0)

Cogency pioneered a revolutionary streaming architecture: **"You're not building a streamable agent. You're building an agent defined by its stream."**

- Every node is an **async generator** that yields thinking steps in real-time
- Stream IS the execution, not a view of it
- Natural cancellation, unified interfaces, and transparent reasoning
- Configurable yield intervals for rate limiting

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

Supports multiple LLM providers with automatic key rotation:

```python
# OpenAI
from cogency.llm import OpenAILLM
llm = OpenAILLM(api_keys="your-key", model="gpt-4")

# Anthropic Claude
from cogency.llm import AnthropicLLM
llm = AnthropicLLM(api_keys="your-key", model="claude-3-sonnet-20240229")

# Google Gemini
from cogency.llm import GeminiLLM
llm = GeminiLLM(api_keys="your-key", model="gemini-1.5-pro")

# Grok (X.AI)
from cogency.llm import GrokLLM
llm = GrokLLM(api_keys="your-key", model="grok-beta")

# Mistral
from cogency.llm import MistralLLM
llm = MistralLLM(api_keys="your-key", model="mistral-large-latest")

# Multiple keys with automatic rotation (all providers)
llm = OpenAILLM(api_keys=["key1", "key2", "key3"])
```

All LLM providers support:
- **Streaming execution** for real-time output
- **Key rotation** for high-volume usage
- **Rate limiting** via yield_interval parameter
- **Unified interface** - switch providers with one line

## Conversation History

Cogency supports conversation history with optional sliding window:

```python
from cogency.context import Context

# Create context with conversation history limit
context = Context("Hello", max_history=10)  # Keep last 10 messages

# Run multiple interactions with shared context
result1 = await agent.run("What's 2+2?", context=context)
result2 = await agent.run("What about 3+3?", context=context)  # Remembers previous exchange

# Access conversation state
print(f"Messages in context: {len(agent.context.messages)}")
print(f"Full conversation: {agent.context.get_clean_conversation()}")

# Continue conversation across multiple runs
result3 = await agent.run("Add those two results together", context=context)
```

**Key features:**
- **Sliding window**: Automatically trims old messages when `max_history` is reached
- **Context persistence**: Reuse contexts across multiple `agent.run()` calls  
- **Context access**: Inspect conversation state via `agent.context` property
- **Clean output**: `get_clean_conversation()` filters internal messages

## Execution Tracing

Enable detailed tracing to see your agent's reasoning:

```python
# Simple trace viewing
result = await agent.run("Complex task", enable_trace=True, print_trace=True)

# Or capture trace data
result = await agent.run("Complex task", enable_trace=True)
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
result = await agent.run("Calculate abc + def")
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
result = await agent.run("Tell me about recent AI developments")

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