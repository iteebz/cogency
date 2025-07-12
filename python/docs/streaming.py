"""
Streaming-First Architecture Design for Cogency

The key insight: "You're not building a streamable agent. You're building an agent defined by its stream."

CURRENT PROBLEM:
- Trying to retrofit streaming onto non-streaming architecture
- Reverse-engineering what happened from traces  
- Complex brittle plumbing between execution and observation
- Traces are a separate concern from the actual execution

SOLUTION: Stream-Native Architecture
The stream IS the execution, not a view of it.

DESIGN PRINCIPLES:
1. Nodes naturally yield their thinking process as they execute
2. LangGraph propagates those yields upward through app.astream()
3. Agent becomes a simple pass-through of the execution stream
4. Trace generation consumes the same stream as external users

IMPLEMENTATION PLAN:

1. Convert all node functions to async generators:
   ```python
   async def plan(state, llm, tools):
       yield {"type": "thinking", "content": "Analyzing request..."}
       
       # LLM streaming
       response_chunks = []
       async for chunk in llm.stream(messages):
           yield {"type": "chunk", "content": chunk}
           response_chunks.append(chunk)
       
       result = "".join(response_chunks)
       yield {"type": "result", "data": {"action": "direct_response", "answer": result}}
       
       return updated_state
   ```

2. Modify LangGraph integration to propagate node yields:
   - LangGraph's astream() should naturally propagate yields from node generators
   - Each node yield flows through to Agent.stream()

3. Simplify Agent.stream() to pass-through:
   ```python
   async def stream(self, message):
       async for step in self.app.astream(initial_state):
           # step contains both LangGraph state updates AND node yields
           yield step
   ```

4. Unified consumption:
   ```python
   # External usage
   async for chunk in agent.stream("task"):
       if chunk["type"] == "thinking":
           print(f"💭 {chunk['content']}")
       elif chunk["type"] == "chunk": 
           print(chunk["content"], end="")
       elif chunk["type"] == "result":
           print(f"✅ {chunk['data']}")
   
   # Trace generation uses same stream
   execution_trace = []
   async for chunk in agent.stream("task"):
       execution_trace.append(chunk)
   ```

BENEFITS:
- No retrofit complexity - streaming is the native execution model
- Real-time visibility into agent thinking
- Unified interface for both streaming and trace collection
- Natural cancellation support (stream stops when cancelled)
- Clean separation: nodes focus on logic, yields handle communication
- Eliminates trace/execution synchronization issues

CHUNK TYPES:
- {"type": "thinking", "content": "..."} - Node reasoning
- {"type": "chunk", "content": "..."} - LLM streaming chunks  
- {"type": "result", "data": {...}} - Node final output
- {"type": "tool_call", "data": {...}} - Tool execution
- {"type": "error", "content": "..."} - Error messages

IMPLEMENTATION STATUS:
✅ Added streaming to BaseLLM interface  
✅ Implemented GeminiLLM.stream() with real-time chunks
✅ Created plan_streaming() as pilot async generator node
✅ Added Agent.stream() as pass-through interface
✅ Switched from LangChain to native google.generativeai for true streaming
✅ Documented streaming-first architecture

NEXT STEPS:
- Convert remaining nodes (reason, act, reflect, respond) to async generators
- Integrate with LangGraph's streaming capabilities
- Build unified trace consumption from same stream
- Add comprehensive streaming test suite

BREAKTHROUGH ACHIEVED:
We've fundamentally shifted from "execution + observation" to "execution = stream"
The agent is now defined by its stream of consciousness, not post-hoc analysis.

This architecture makes the agent transparent - users see the actual thought 
process as it happens, not a reconstruction of what occurred.
"""