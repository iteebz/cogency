# CLI

Cogency's command-line interface for instant productivity.

## Quick Start

```bash
pip install cogency
cogency init hello-world
cd hello-world && python main.py
```

## Commands

### `cogency tools`
List all available tools with descriptions.

```bash
cogency tools
```

**Output:**
```
🔧 Available Cogency Tools

Core Tools:
  📁 files      - Local filesystem I/O (create, read, edit, list)
  💻 shell      - System command execution
  🌐 http       - HTTP requests and API calls
  📖 scrape     - Web content extraction
  🔍 search     - Web search and information discovery

Total: 5 core tools available

Usage: Agent('assistant', tools=['files', 'shell'])
```

### `cogency init <name>`
Create a new Cogency project with scaffolding.

```bash
cogency init my-agent
```

Creates:
```
my-agent/
├── main.py           # Agent with examples
├── pyproject.toml    # Dependencies
└── README.md         # Getting started guide
```

**Generated `main.py`:**
```python
from cogency import Agent

# Create your agent (works out-of-box with Ollama)
agent = Agent(
    name="assistant",
    tools=["files", "shell"],
    identity="You are a helpful AI assistant."
)

# Production providers (requires extras):
# agent = Agent("assistant", llm="gemini")    # pip install cogency[gemini]
# agent = Agent("assistant", llm="anthropic") # pip install cogency[anthropic]

# Custom OpenAI-compatible endpoint:
# import os
# os.environ["OPENAI_BASE_URL"] = "http://localhost:11434/v1"  # Ollama
# os.environ["OPENAI_API_KEY"] = "ollama"

# Interactive mode
if __name__ == "__main__":
    import asyncio
    
    async def main():
        while True:
            query = input("\n> ")
            if query.lower() in ["exit", "quit"]:
                break
            
            response = await agent.run_async(query)
            print(f"🤖 {response}")
    
    asyncio.run(main())
```

### `cogency <message>`
Run a one-off agent query.

```bash
cogency "What's the weather like?"
```

### `cogency -i`
Interactive mode for ongoing conversations.

```bash
cogency -i
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

## Examples

### Create Project
```bash
cogency init trading-agent
cd trading-agent
pip install cogency
python main.py
```

### Discover Tools
```bash
cogency tools
# See all available tools: files, shell, http, scrape, search
```

### Quick Query
```bash
cogency "List files in current directory"
```

### Interactive Session
```bash
cogency -i
> Help me analyze this log file
> Create a summary report
> exit
```