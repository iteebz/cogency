# Provider Configuration Limitation

## Issue
The current Agent constructor doesn't support separate `llm` and `embed` provider configuration, limiting flexibility for cost optimization and performance tuning.

## Current Behavior
```python
# ❌ This should work but doesn't:
Agent("assistant", llm="gemini", embed="nomic")  # ValidationError: Unknown config keys: llm

# ✅ This works but limits you to one provider:
Agent("assistant", provider="gemini")  # Uses Gemini for both LLM and embedding

# ✅ This works for embedding override only:
Agent("assistant", provider="gemini", embed="nomic")  # Gemini LLM + Nomic embedding
```

## Root Cause
- `src/cogency/config/validation.py` line 20: `"provider": None` ✅
- `src/cogency/config/validation.py` line 21: `"embed": None` ✅  
- Missing: `"llm": None` ❌

- `src/cogency/runtime.py` line 21: `llm = AgentSetup.llm(config.llm)` expects `config.llm`
- But Agent constructor validation rejects `llm` parameter

## Impact
Users cannot optimize costs by mixing providers:
- **Expensive**: `provider="openai"` (GPT-4 + OpenAI embedding)
- **Cheap**: Want `llm="openai", embed="nomic"` (GPT-4 + free Nomic embedding)
- **Performance**: Want `llm="gemini", embed="local"` (cloud LLM + local embedding)

## Workaround
For now, use provider instances directly:
```python
from cogency.providers.gemini import Gemini
Agent("assistant", provider=Gemini(api_keys=["key1", "key2"]))
```

## Fix Required
Add `"llm": None` to `validation.py` known_keys and update setup logic to handle separate LLM configuration.

---
*This limitation blocks optimal provider mixing and should be addressed in next release.*