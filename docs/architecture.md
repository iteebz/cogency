# architecture

## react reasoning loop

Cogency agents use **ReAct** (Reason-Act-Observe) for multi-step reasoning with preprocess node and decomposed implementation:

```
🔧 PREPROCESS → 🧠 REASON → ⚡ ACT → 👀 OBSERVE
```

### implementation: decomposed nodes

The ReAct loop is implemented through focused, single-responsibility nodes:

1. **preprocess**: tool subsetting, memory operations, routing (ReAct vs direct respond)
2. **reason**: strategy determination and action planning  
3. **act**: tool execution with parallel processing and error handling
4. **observe**: process tool outputs and decide next steps
5. **respond**: final answer generation with context integration

The preprocess node intelligently routes simple queries directly to respond, while complex queries enter the full ReAct loop.

### streaming execution

Each node streams live updates for complete transparency:

```python
async for chunk in agent.stream("complex query"):
    print(chunk, end="", flush=True)
# Shows: 🔧 PREPROCESS → 🧠 REASON → ⚡ ACT → 👀 OBSERVE → 💬 RESPOND
```

### tool ecosystem

Built-in tools auto-register with zero ceremony:

- **🧮 Calculator** - Mathematical expressions and computations
- **🌐 Web Search** - DuckDuckGo search with result processing
- **📁 File Manager** - Read, write, manage files with validation
- **🌡️ Weather** - Current conditions and forecasts
- **🕒 Datetime** - Timezone-aware time operations
- **📊 CSV Tools** - Data processing and analysis
- **🗄️ SQL Tools** - Database querying and management
- **💻 Shell Tools** - System command execution
- **🐍 Code Execution** - Python code evaluation in sandboxed environment