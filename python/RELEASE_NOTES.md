# Cogency v0.2.2 Release Notes

## Bug Fixes & Stability Improvements

### 🔧 Core Framework Stability
- **Fixed infinite recursion issues**: Resolved "Recursion limit of 25 reached" errors that occurred during complex multi-step workflows
- **Improved conversation history preservation**: Fixed critical bug where reason node was losing conversation context, causing repeated identical actions
- **Enhanced routing logic**: Implemented elegant solution where REASON routes directly to RESPOND when no valid tool call is present, eliminating N/A tool routing issues

### 🎨 Trace Output & User Experience
- **Cleaner trace formatting**: Removed timing calculations from trace output for a more beautiful, focused display
- **Eliminated redundant prefixes**: Fixed "Reasoning:" appearing multiple times in output
- **Real-time execution feedback**: Added streaming trace output showing agent progress as it works
- **Simplified execution messages**: Clean, intuitive messages like "Executing calculation..." and "Searching the web..."

### 🔌 API Improvements
- **Cleaner LLM interface**: LLM class now accepts either `str` or `List[str]` for API keys with automatic key rotation
- **Configurable execution limits**: Added `max_depth` parameter to Agent constructor (default: 10) for better loop control
- **Improved error handling**: More robust JSON parsing and graceful degradation patterns

### 🛠️ Developer Experience
- **Enhanced prompts**: Streamlined PLAN prompt to encourage proper JSON responses and reduce parsing errors
- **Better test coverage**: Added comprehensive test suite for infinite recursion prevention (135 tests passing)
- **Code quality**: Fixed all critical linting issues and improved type safety

## Technical Details

### Breaking Changes
- `GeminiLLM` constructor now accepts `Union[str, List[str]]` for `api_keys` parameter
- Automatic `KeyRotator` creation when multiple API keys are provided

### Migration Guide
```python
# Before
from cogency.utils.key_rotator import KeyRotator
keys = ["key1", "key2", "key3"] 
key_rotator = KeyRotator(keys)
llm = GeminiLLM(key_rotator=key_rotator)

# After (cleaner interface)
llm = GeminiLLM(api_keys=["key1", "key2", "key3"])  # Automatic rotation
# or single key
llm = GeminiLLM(api_keys="single_key")
```

### New Features
- Configurable `max_depth` parameter in Agent constructor
- Real-time trace streaming with `trace_mode=True`
- Enhanced file management with `FileManagerTool`

## Dependencies
- Maintained compatibility with Python 3.9-3.12
- No new external dependencies added

---

**Full Changelog**: [View on GitHub](https://github.com/iteebz/cogency/compare/v0.2.1...v0.2.2)

**Installation**: `pip install cogency==0.2.2`