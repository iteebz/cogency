"""Simple execution loop - no LangGraph ceremony."""

from cogency.phases.act import act
from cogency.phases.preprocess import preprocess
from cogency.phases.reason import reason
from cogency.phases.respond import respond
from cogency.resilience import robust
from cogency.state import State


async def run_agent(state: State, **kwargs) -> State:
    """Simple execution loop using resilience decorators."""
    
    # Extract kwargs needed by different phases
    llm = kwargs.get("llm")
    tools = kwargs.get("tools", [])
    memory = kwargs.get("memory")
    system_prompt = kwargs.get("system_prompt")
    identity = kwargs.get("identity")
    json_schema = kwargs.get("json_schema")
    
    # Preprocessing step
    state = await preprocess(
        state,
        llm=llm,
        tools=tools,
        memory=memory,
        system_prompt=system_prompt,
        identity=identity
    )
    
    # Main reasoning loop
    while state.iteration < state.max_iterations:
        # Reason about what to do
        state = await reason(
            state,
            llm=llm,
            tools=tools,
            system_prompt=system_prompt,
            identity=identity
        )
        
        # If no tools needed, break to response
        if not state.tool_calls:
            break
            
        # Execute tools
        state = await act(state, tools=tools)
        
        # Increment iteration
        state.iteration += 1
        
        # Check stop conditions
        if state.stop_reason:
            break
    
    # Generate final response
    state = await respond(
        state,
        llm=llm,
        tools=tools,
        system_prompt=system_prompt,
        identity=identity,
        json_schema=json_schema
    )
    
    return state


# Alternative with resilience decorators (when we re-enable them)
async def run_agent_robust(state: State, **kwargs) -> State:
    """Execution loop with @robust decorators."""
    
    state = await robust.preprocess(state, **kwargs)
    
    while state.iteration < state.max_iterations:
        state = await robust.reason(state, **kwargs)
        if not state.tool_calls:
            break
        state = await robust.act(state, **kwargs) 
        state.iteration += 1
        if state.stop_reason:
            break
    
    return await robust.respond(state, **kwargs)