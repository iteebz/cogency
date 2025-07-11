# Cogency

> **Agentic AI out of the box**

Cogency makes it dead simple to build multi-step reasoning agents. No complex configurations, no verbose setup - just clean, extensible agents that work.

## Quick Start

```python
from cogency.agent import Agent
from cogency.llm import GeminiLLM
from cogency.tools.calculator import CalculatorTool

llm = GeminiLLM(api_key="your-key")
agent = Agent(name="MyAgent", llm=llm, tools=[CalculatorTool()])

result = agent.run("What is 15 * 23?", enable_trace=True)
print(result["response"])
```

## Why Cogency?

- **Zero config** - Agents in 6 lines of code
- **Auto-discovery** - Drop tools in `/tools/` and they just work
- **Clean tracing** - See exactly what your agent is thinking
- **Multi-step reasoning** - Built-in plan → reason → act → reflect → respond loop
- **Extensible** - Add new LLMs and tools easily

## Language Support

- **Python** - Full-featured implementation
- **JavaScript** - Coming soon

## Installation

```bash
# Python
pip install cogency

# JavaScript (coming soon)
npm install cogency
```

## Documentation

- [Python Documentation](./python/README.md)
- [JavaScript Documentation](./js/README.md) (coming soon)

## Example Output

```
> What is 64/6?
🤖 64 divided by 6 is approximately 10.67.

--- Execution Trace (ID: 6e84519b) ---
PLAN     | The user is asking a division problem, requires calculation.
REASON   | TOOL_CALL: calculator(operation='divide', num1=64, num2=6)
ACT      | calculator -> {'result': 10.666666666666666}
REFLECT  | Division calculation completed successfully.
RESPOND  | 64 divided by 6 is approximately 10.67.
--- End Trace ---
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.