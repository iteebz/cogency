# LLM Provider Setup

Cogency auto-detects your LLM provider from environment variables. Just set one and go.

## Environment Variables

```bash
# Any one of these - Cogency auto-detects
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=your-key-here
MISTRAL_API_KEY=your-key-here
GROK_API_KEY=your-key-here
```

## Explicit LLM Configuration

```python
from cogency import Agent
from cogency.llm import OpenAILLM, AnthropicLLM, GeminiLLM

# OpenAI
agent = Agent("assistant", llm=OpenAILLM(
    api_key="sk-...",
    model="gpt-4o",  # Optional, defaults to gpt-4o
    temperature=0.7   # Optional
))

# Anthropic
agent = Agent("assistant", llm=AnthropicLLM(
    api_key="sk-ant-...",
    model="claude-3-5-sonnet-20241022"  # Optional
))

# Gemini
agent = Agent("assistant", llm=GeminiLLM(
    api_key="your-key",
    model="gemini-1.5-pro"  # Optional
))
```

## Model Selection

Each provider supports multiple models:

```python
# OpenAI models
OpenAILLM(model="gpt-4o")           # Default, best overall
OpenAILLM(model="gpt-4o-mini")      # Faster, cheaper
OpenAILLM(model="gpt-4-turbo")      # Previous generation

# Anthropic models  
AnthropicLLM(model="claude-3-5-sonnet-20241022")  # Default, best reasoning
AnthropicLLM(model="claude-3-5-haiku-20241022")   # Faster, cheaper

# Gemini models
GeminiLLM(model="gemini-1.5-pro")    # Default, best overall
GeminiLLM(model="gemini-1.5-flash")  # Faster, cheaper
```

## Custom LLM

Implement your own LLM provider:

```python
from cogency.llm.base import BaseLLM

class MyLLM(BaseLLM):
    async def generate(self, messages, **kwargs):
        # Your LLM integration
        return "Generated response"
    
    async def generate_stream(self, messages, **kwargs):
        # Your streaming implementation
        yield "Streaming"
        yield " response"

agent = Agent("assistant", llm=MyLLM())
```

## Testing with Mock LLM

```python
from cogency.llm import MockLLM

# For testing - returns predictable responses
agent = Agent("test", llm=MockLLM())
```