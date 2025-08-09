# Providers

Internal provider architecture for contributors.

## Architecture

**Option A Pattern**: Universal params in base class, provider-specific params in subclasses.

```python
class LLM(ABC):
    def __init__(self, model=None, temperature=0.7, max_tokens=16384, **kwargs):
        # Parameter validation
        if model is None:
            raise ValueError(f"{self.__class__.__name__} must specify a model")
        if not (0.0 <= temperature <= 2.0):
            raise ValueError("temperature must be between 0.0 and 2.0")
        
        # Auto-derive provider name
        self.provider_name = self.__class__.__name__.lower()
        self.keys = KeyManager.for_provider(self.provider_name, api_keys)

class OpenAI(LLM):
    def __init__(self, model="gpt-4o-mini", temperature=0.7, max_tokens=16384,
                 top_p=1.0, frequency_penalty=0.0, presence_penalty=0.0, **kwargs):
        super().__init__(model=model, temperature=temperature, max_tokens=max_tokens, **kwargs)
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty
```

## Base Classes

### LLM Base (`providers/llm/base.py`)

**Universal Parameters:**
- `model: str = None` (must be set by provider)
- `temperature: float = 0.7` (0.0-2.0)
- `max_tokens: int = 16384` (1-100000)
- `timeout: float = 15.0` (0-300)
- `max_retries: int = 3`
- `enable_cache: bool = True`

**Features:**
- Auto-derived provider names via `self.__class__.__name__.lower()`
- Automatic key rotation via `KeyManager`
- Parameter validation with clear error messages
- Metrics and cost tracking
- Caching support

### Embed Base (`providers/embed/base.py`)

**Universal Parameters:**
- `model: str = None` (must be set by provider)
- `dimensionality: int = None` (must be positive)
- `timeout: float = 15.0` (0-300)
- `max_retries: int = 3`

**Features:**
- Same auto-derivation and validation as LLM
- Batch processing support via `embed_array()`
- Legacy compatibility for existing code

## Provider Implementation

### Adding New LLM Provider

1. **Create provider file**: `providers/llm/newprovider.py`
2. **Implement required methods**: `_get_client()`, `_run_impl()`, `_stream_impl()`
3. **Define constructor with defaults**:

```python
class NewProvider(LLM):
    def __init__(self, 
                 model="best-model-v1",
                 temperature=0.7,
                 max_tokens=16384,
                 provider_param=default_value,
                 **kwargs):
        super().__init__(model=model, temperature=temperature, max_tokens=max_tokens, **kwargs)
        self.provider_param = provider_param

    def _get_client(self):
        return NewProviderClient(api_key=self.next_key())

    async def _run_impl(self, messages, **kwargs):
        client = self._get_client()
        response = await client.complete(
            model=self.model,
            messages=self._format(messages),
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            provider_param=self.provider_param,
            **kwargs
        )
        return response.text
```

### Adding New Embedding Provider

Similar pattern with `embed()` method instead of `_run_impl()`.

## Design Principles

### Parameter Philosophy
- **Provider-native parameters**: No hidden translation layers
- **Explicit over implicit**: All parameters declared in constructor
- **Validation at creation**: Fail fast with clear error messages
- **Provider authenticity**: Respect official API parameter names

### Why No Standardization?
1. **Semantic precision**: `top_p` means different things to different models
2. **Provider authenticity**: Developers expect official parameter names
3. **Future compatibility**: New provider parameters don't break abstraction
4. **Debugging clarity**: Error messages use original parameter names

### Model Defaults Strategy
- **Cost-aware**: Default to most cost-effective capable model
- **Capability-balanced**: Avoid slowest/fastest extremes
- **Current**: Update defaults as new models release

## Current Defaults

**LLM Models:**
- OpenAI: `gpt-4o-mini` (cost-optimized)
- Anthropic: `claude-3-5-haiku-20241022` (fast + capable)
- Mistral: `mistral-small-latest` (good value)
- Gemini: `gemini-2.0-flash-exp` (latest experimental)
- Ollama: `llama3.3` (best local)

**Embedding Models:**
- Nomic: `nomic-embed-text-v2-moe` (MoE cost optimization)
- OpenAI: `text-embedding-3-small` (balanced)
- Mistral: `mistral-embed` (consistent with LLM)

## Testing

Provider tests should verify:
1. **Parameter validation**: Invalid ranges rejected
2. **Constructor defaults**: Correct model/parameter defaults
3. **API propagation**: Constructor params reach API calls
4. **Key rotation**: Multiple keys rotate correctly
5. **Error handling**: Graceful failure modes

## Common Issues

### Parameter Propagation
Ensure all constructor parameters are passed to API calls:

```python
# ✅ Good - uses self.provider_param
response = await client.complete(
    provider_param=self.provider_param,
    **kwargs
)

# ❌ Bad - hardcoded or missing
response = await client.complete(
    provider_param="hardcoded",  # Wrong
    **kwargs
)
```

### Validation Ranges
Use realistic bounds:

```python
# ✅ Good - practical ranges
if not (0.0 <= temperature <= 2.0):
    raise ValueError("temperature must be between 0.0 and 2.0")

# ❌ Bad - too restrictive
if not (0.1 <= temperature <= 1.0):  # Excludes valid 0.0 and 1.5
```

### Error Handling
Raise exceptions in streaming, don't silently return:

```python
# ✅ Good
except Exception as e:
    raise e

# ❌ Bad
except Exception as e:
    return  # Silent failure
```