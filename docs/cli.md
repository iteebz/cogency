# CLI

*Note: A command-line interface is planned for future release. Currently, Cogency is a Python library.*

## Quick Start

```python
from cogency import Agent

agent = Agent("assistant")
result = agent.run("What's 2+2?")
print(result)  # "4"
```

## Provider Configuration

### Zero Ceremony (Default)
Works immediately with Ollama:

```bash
pip install cogency
# Uses OpenAI client → connects to Ollama automatically
```

### Production Providers
Install extras for advanced providers:

```bash
pip install cogency[gemini]     # Google Gemini
pip install cogency[anthropic]  # Claude
pip install cogency[mistral]    # Mistral AI
```

### Local Development
Configure Ollama endpoint:

```bash
export OPENAI_BASE_URL="http://localhost:11434/v1"
export OPENAI_API_KEY="ollama"
```

## Interactive Example

```python
from cogency import Agent

agent = Agent(
    "assistant",
    tools=["files", "shell"],
    identity="You are a helpful AI assistant."
)

# Interactive mode
if __name__ == "__main__":
    while True:
        query = input("\n> ")
        if query.lower() in ["exit", "quit"]:
            break
        
        response = agent.run(query)
        print(f"🤖 {response}")
```