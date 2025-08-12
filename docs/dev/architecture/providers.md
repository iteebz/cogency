# Providers

Internal provider architecture for contributors.

## Architecture

**Unified Provider Pattern**: Single Provider ABC supporting both LLM and embedding capabilities.

```python
class Provider(ABC):
    def __init__(self, model=None, temperature=0.7, max_tokens=16384, **kwargs):
        # Universal parameters
        self.model = model or self._get_default_model()
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Auto-derive provider name and key management
        self.provider_name = self.__class__.__name__.lower()
        self.keys = KeyManager.for_provider(self.provider_name, api_keys)
        
    @abstractmethod
    async def run(self, messages: List[Dict[str, str]], **kwargs) -> Result:
        """Generate LLM response."""
        
    @abstractmethod  
    async def stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncIterator[str]:
        """Generate streaming LLM response."""
        
    async def embed(self, text: Union[str, List[str]], **kwargs) -> Result:
        """Generate embeddings (if supported)."""
        raise NotImplementedError(f"{self.provider_name} does not support embeddings")

class OpenAI(Provider):
    def __init__(self, llm_model="gpt-4o-mini", embed_model="text-embedding-3-small",
                 dimensionality=1536, temperature=0.7, max_tokens=16384, **kwargs):
        super().__init__(model=llm_model, temperature=temperature, max_tokens=max_tokens, **kwargs)
        self.embed_model = embed_model
        self.dimensionality = dimensionality
```

## Base Class

### Provider ABC (`providers/base.py`)

**Universal Parameters:**
- `model: str` (primary model - LLM model for dual-capability providers)
- `temperature: float = 0.7` (0.0-2.0)
- `max_tokens: int = 16384` (1-100000)
- `timeout: float = 30.0` (0-300)
- `max_retries: int = 3`
- `enable_cache: bool = False`

**Provider-Specific Parameters:**
- `llm_model: str` - LLM model name (semantic parameter)
- `embed_model: str` - Embedding model name (semantic parameter) 
- `dimensionality: int` - Embedding dimensions
- Provider-specific API parameters

**Features:**
- Auto-derived provider names via `self.__class__.__name__.lower()`
- Automatic key detection and rotation via `KeyManager`
- Parameter validation with clear error messages
- Unified caching for both LLM and embedding responses
- Capability-based method implementation
- Resilient error handling with Result pattern

## Provider Implementation

### Adding New Provider

1. **Create provider file**: `providers/newprovider.py`
2. **Implement required methods**: `_get_client()`, `run()`, `stream()`, optionally `embed()`
3. **Define constructor with semantic parameters**:

```python
class NewProvider(Provider):
    def __init__(self, 
                 llm_model="best-llm-v1",
                 embed_model="best-embed-v1", 
                 dimensionality=768,
                 temperature=0.7,
                 max_tokens=16384,
                 provider_param=default_value,
                 **kwargs):
        # Pass primary model (LLM) to base class
        super().__init__(model=llm_model, temperature=temperature, max_tokens=max_tokens, **kwargs)
        # Store semantic parameters
        self.embed_model = embed_model
        self.dimensionality = dimensionality
        self.provider_param = provider_param

    def _get_client(self):
        return NewProviderClient(api_key=self.next_key(), timeout=self.timeout)

    async def run(self, messages: List[Dict[str, str]], **kwargs) -> Result:
        # Check cache, get client, make API call, emit metrics, cache result
        client = self._get_client()
        response = await client.chat(
            model=self.model,
            messages=self._format(messages),
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            provider_param=self.provider_param,
            **kwargs
        )
        return Ok(response.text)

    async def stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncIterator[str]:
        client = self._get_client()
        async for chunk in client.stream_chat(...):
            if chunk.text:
                yield chunk.text
                
    async def embed(self, text: Union[str, List[str]], **kwargs) -> Result:
        # Optional - only implement if provider supports embeddings
        client = self._get_client()
        response = await client.embed(
            input=text,
            model=self.embed_model,
            dimensions=self.dimensionality,
            **kwargs
        )
        return Ok([np.array(emb) for emb in response.embeddings])
```

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
- Anthropic: `claude-3-5-haiku` (fast + capable)
- Mistral: `mistral-small-latest` (good value)
- Gemini: `gemini-2.0-flash-exp` (latest experimental)
- OpenRouter: `anthropic/claude-3.5-haiku` (cost routing)
- Groq: `llama-3.3-70b-versatile` (fast inference)
- Ollama: `llama3.3` (best local)

**Embedding Models:**
- Nomic: `nomic-embed-text-v1.5` (high quality)
- OpenAI: `text-embedding-3-small` (balanced)
- Mistral: `mistral-embed` (consistent with LLM)
- Gemini: `gemini-embedding-001` (Google integration)

## Testing

Provider tests should verify:
1. **Automatic key detection**: Provider initializes with environment keys
2. **Core LLM functionality**: `run()` and `stream()` work correctly
3. **Embedding capability**: `embed()` works for providers that support it
4. **Caching**: Cached responses return faster
5. **Parameter validation**: Invalid ranges rejected appropriately
6. **Error handling**: Graceful failure with proper Result patterns

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