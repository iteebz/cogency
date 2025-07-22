# Architecture

## AdaptReAct: The Key Innovation

**Preprocess → Reason → Act → Respond**

```
🔧 PREPROCESS → 🧠 REASON → ⚡ ACT → 💬 RESPOND
     ↓              ↓         ↓
   respond      respond    reason
```

The **preprocess node** is what makes everything work:

### Tool Subsetting
- Registry holds 100+ tools
- Preprocess intelligently selects 3-5 relevant ones
- Keeps system extensible without overwhelming the LLM

### Memory Operations  
- Extracts memory-worthy information ("Remember I like Python")
- Only `recall` tool enters ReAct loop
- Clean separation of concerns

### Intelligent Routing
- Simple queries → direct `respond`
- Tool-requiring queries → `reason` (Fast React)
- Complex analysis → `reason` (Deep React with reflection)

## Zero-Ceremony Tool System

```python
@tool
class MyTool(BaseTool):
    def __init__(self):
        super().__init__("my_tool", "Does something useful")
    
    async def run(self, param: str):
        return {"result": f"Processed: {param}"}
```

- Auto-registers via `@tool` decorator
- Schema and examples derived automatically  
- No boilerplate, no duplicate definitions
- Drop in 100 tools - preprocess picks what's needed

## Built-in Tools

Auto-register with `@tool` decorator:

🧮 Calculator • 🌐 Search • 📁 Files • 🌡️ Weather • 🕒 Time • 📊 CSV • 🗄️ SQL • 💻 Shell • 🐍 Code

## Memory Backends

- **Filesystem**: Default, zero-config
- **ChromaDB**: Vector search
- **Pinecone**: Cloud vector database  
- **PGVector**: PostgreSQL with vector extensions