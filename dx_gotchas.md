# DX Gotchas & Hidden Ceremony

## 🚨 DISCOVERED ISSUES

### 1. Missing `psutil` Dependency
**Impact**: Complete framework failure
**Root Cause**: `CogencyProfiler` imports `psutil` but it's not in dependencies
**Status**: CRITICAL - Breaks all imports

```python
# File: src/cogency/utils/profiling.py:4
import psutil  # ❌ Missing dependency
```

### 2. Profiling Import Everywhere
**Impact**: Adds startup overhead and dependency complexity
**Root Cause**: Profiling is imported in core modules instead of being optional
**Status**: ARCHITECTURE ISSUE

```python
# File: src/cogency/memory/filesystem.py:14
from ..utils.profiling import CogencyProfiler  # ❌ Always imported

# File: src/cogency/utils/tool_execution.py:9
from cogency.utils.profiling import CogencyProfiler  # ❌ Always imported
```

### 3. Circular Import Risk
**Impact**: Fragile import structure
**Root Cause**: Deep import chains without lazy loading
**Status**: ARCHITECTURE ISSUE

```
cogency → agent → llm → utils → tools → memory → profiling
```

### 4. Heavy Monitoring Import
**Impact**: Adds 10+ modules to import path
**Root Cause**: Monitoring is always imported, not optional
**Status**: PERFORMANCE ISSUE

```python
# File: src/cogency/agent.py:11
from cogency.monitoring import get_monitor  # ❌ Always imported
```

### 5. Missing Production Dependencies
**Impact**: Framework unusable in production
**Root Cause**: Missing `psutil` for monitoring
**Status**: CRITICAL

## 🎯 MEASURED OVERHEAD

### Current State (BROKEN):
- **Import Time**: FAILED (missing psutil)
- **Agent Creation**: FAILED (missing psutil)
- **Hello World**: FAILED (missing psutil)
- **Memory Usage**: FAILED (missing psutil)
- **Installation**: FAILED (dependency issues)

### Expected After Fix:
- **Import Time**: ~200ms (heavy monitoring stack)
- **Agent Creation**: ~50ms (LLM initialization)
- **Memory Usage**: ~30MB (monitoring overhead)

## 🔧 REQUIRED FIXES

### 1. Add Missing Dependencies
```toml
# pyproject.toml
dependencies = [
    # ... existing
    "psutil>=5.9.0",  # CRITICAL: Add this
]
```

### 2. Make Profiling Optional
```python
# Optional profiling pattern
try:
    from cogency.utils.profiling import CogencyProfiler
    PROFILING_ENABLED = True
except ImportError:
    PROFILING_ENABLED = False
    
    class MockProfiler:
        async def profile_tool_execution(self, func):
            return await func()
```

### 3. Lazy Load Monitoring
```python
# Lazy monitoring pattern
def get_monitor():
    if not hasattr(get_monitor, '_monitor'):
        get_monitor._monitor = CogencyMonitor()
    return get_monitor._monitor
```

### 4. Streamline Imports
```python
# Remove unnecessary imports from core paths
# Move profiling to optional extension
# Use lazy loading for heavy components
```

## 🏆 WORLD-CLASS DX REQUIREMENTS

### What Works:
- Clean API design (`Agent("name")`)
- Async-first architecture  
- Auto-discovery patterns

### What's Broken:
- ❌ Missing dependencies break everything
- ❌ Heavy import overhead
- ❌ Profiling not optional
- ❌ No graceful degradation

### DX Verdict:
**CURRENT**: 👎 BROKEN (0/8 tests pass)
**POTENTIAL**: 🎉 WORLD-CLASS (after dependency fixes)

## 📋 REMEDIATION PLAN

1. **IMMEDIATE**: Add `psutil` to dependencies
2. **URGENT**: Make profiling optional with fallbacks
3. **IMPORTANT**: Implement lazy loading for monitoring
4. **NICE-TO-HAVE**: Optimize import paths

**ETA**: 15 minutes to fix critical issues
**Impact**: 100% → 95% test pass rate