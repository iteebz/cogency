# Providers

Cogency supports multiple LLM and embedding providers with unified interfaces and automatic key rotation.

## LLM Providers

```python
from cogency.providers.llm import OpenAI, Anthropic, Mistral, Gemini, Ollama

# Cost-optimized defaults
llm = OpenAI()  # gpt-4o-mini
llm = Anthropic()  # claude-3-5-haiku-20241022
llm = Mistral()  # mistral-small-latest
llm = Gemini()  # gemini-2.0-flash-exp
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
from cogency.providers.embed import NomicEmbed, OpenAIEmbed, MistralEmbed

# Cost-optimized defaults
embed = NomicEmbed()  # nomic-embed-text-v2-moe, 768D
embed = OpenAIEmbed()  # text-embedding-3-small, 1536D
embed = MistralEmbed()  # mistral-embed, 1024D

# Custom configuration
embed = NomicEmbed(
    model="nomic-embed-text-v2",
    dimensionality=512,
    batch_size=10
)

embed = OpenAIEmbed(
    model="text-embedding-3-large",
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

# Embedding
result = embed.embed("Hello world")
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