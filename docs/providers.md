# Providers

Cogency supports multiple LLM and embedding providers with unified interfaces and automatic key rotation.

## LLM Providers

```python
from cogency.providers import OpenAI, Anthropic, Mistral, Gemini, Ollama, OpenRouter, Groq, Nomic

# Cost-optimized defaults
llm = OpenAI()  # gpt-4o-mini
llm = Anthropic()  # claude-3-5-haiku
llm = Mistral()  # mistral-small-latest
llm = Gemini()  # gemini-2.0-flash-exp
llm = OpenRouter()  # anthropic/claude-3.5-haiku
llm = Groq()  # llama-3.3-70b-versatile
llm = Ollama()  # llama3.3

# Custom configuration
llm = OpenAI(
    model="gpt-4o",
    temperature=0.5,
    max_tokens=8192,
    top_p=0.9,
    frequency_penalty=0.1,
    presence_penalty=0.1
)

llm = Anthropic(
    model="claude-3-5-sonnet-20241022",
    temperature=0.3,
    max_tokens=4096,
    top_k=20,
    top_p=0.8
)
```

### Universal Parameters
- `model`: Model name (provider-specific)
- `temperature`: Randomness (0.0-2.0)
- `max_tokens`: Output limit (1-100000)
- `timeout`: Request timeout (0-300s)

### Provider-Specific Parameters

**OpenAI**
- `top_p`: Nucleus sampling threshold
- `frequency_penalty`: Penalize token frequency
- `presence_penalty`: Penalize token presence

**Anthropic & Gemini**
- `top_k`: Consider top K tokens
- `top_p`: Nucleus sampling threshold

**Mistral**
- `top_p`: Nucleus sampling threshold

**Ollama**
- `base_url`: Local server URL

## Embedding Providers

```python
# Unified providers support both LLM and embedding
from cogency.providers import OpenAI, Mistral, Gemini, Nomic

# Cost-optimized embedding defaults
embed = Nomic()  # nomic-embed-text-v1.5, 768D
embed = OpenAI()  # text-embedding-3-small, 1536D
embed = Mistral()  # mistral-embed, 1024D
embed = Gemini()  # gemini-embedding-001, 768D

# Custom configuration
embed = Nomic(
    embed_model="nomic-embed-text-v1.5",
    dimensionality=512,
    batch_size=10
)

embed = OpenAI(
    embed_model="text-embedding-3-large",
    dimensionality=3072
)
```

### Universal Parameters
- `model`: Model name
- `dimensionality`: Vector dimensions
- `timeout`: Request timeout (0-300s)

### Provider-Specific Parameters

**Nomic**
- `batch_size`: Processing batch size
- `task_type`: Embedding task type

**OpenAI, Mistral, Gemini**
- Provider-specific embedding models and dimensions

## Key Management

All providers support automatic key rotation:

```python
# Single key (from environment)
llm = OpenAI()  # Uses OPENAI_API_KEY

# Multiple keys for rotation
llm = OpenAI(api_keys=["key1", "key2", "key3"])

# Mixed sources
llm = OpenAI(api_keys=["explicit_key", None])  # Explicit + env
```

Environment variables:
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY` 
- `MISTRAL_API_KEY`
- `GOOGLE_API_KEY`
- `NOMIC_API_KEY`
- `GROQ_API_KEY`
- `OPENROUTER_API_KEY`

## Usage

```python
# LLM generation
messages = [
    {"role": "user", "content": "Hello!"}
]

# Async
response = await llm.run(messages)
print(response.data)

# Streaming
async for chunk in llm.stream(messages):
    print(chunk, end="")

# Embedding (single text)
result = await embed.embed("Hello world")
vectors = result.data  # List of numpy arrays

# Embedding (multiple texts)
result = await embed.embed(["Hello", "world"])
vectors = result.data  # List of numpy arrays
```

## Error Handling

Providers use `resilient_result.Result`:

```python
result = await llm.run(messages)
if result.success:
    print(result.data)
else:
    print(f"Error: {result.error}")
```