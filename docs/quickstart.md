# quickstart

## install

```bash
pip install cogency
```

## hello world

```python
from cogency import Agent

agent = Agent("demo")
await agent.run_streaming("What's the weather in Tokyo?")
```

## with tools

```python
from cogency import Agent, WeatherTool, CalculatorTool

agent = Agent("assistant", tools=[WeatherTool(), CalculatorTool()])
await agent.run_streaming("What's 15 * 23 and weather in London?")
```

## api keys

Create `.env` file:

```bash
# Auto-detects from any available key
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=your-key-here
```

## output modes

- **streaming**: `agent.run_streaming()` - live reasoning traces
- **final**: `agent.run()` - just the final response
- **trace**: `agent.run(mode="trace")` - response + execution trace