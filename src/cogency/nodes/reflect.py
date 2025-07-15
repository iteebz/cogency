from typing import Dict, Any, Optional, List
from cogency.llm import BaseLLM
from cogency.types import AgentState
from cogency.utils import trace
from cogency.tools.base import BaseTool

REFLECT_PROMPT = """
You are a decisive AI assistant evaluating task completion.

ANALYSIS TASK:
1. Review conversation history and tool outputs
2. Check if you have ALL essential information to answer the user's request
3. Determine completion status

DECISION CRITERIA:
- COMPLETE: Have all essential information needed to answer the user's request
- CONTINUE: Missing critical information that tools can provide
- ERROR: Tool failure that blocks completion

BIAS TOWARD COMPLETION:
- If tools provided relevant data, task is likely COMPLETE
- Only continue if missing ESSENTIAL information that tools can provide
- Don't continue for calculations - those can be done in response
- Don't continue for formatting - that's response work

Your output MUST be valid JSON:
{{"status": "complete", "reasoning": "<why task is complete>"}}
{{"status": "continue", "missing": "<what specific information is still needed>", "reasoning": "<why more work needed>"}}
{{"status": "error", "error": "<clear error description>"}}

BE DECISIVE: If you have the core information requested, mark as COMPLETE.
"""


@trace
async def reflect(state: AgentState, *, llm: BaseLLM) -> AgentState:
    """Reflect node evaluates task completion."""
    
    context = state["context"]
    messages = list(context.messages)
    
    messages.insert(0, {"role": "system", "content": REFLECT_PROMPT})

    # Get reflection analysis
    llm_response = await llm.invoke(messages)
    context.add_message("assistant", llm_response)
    
    # Return updated state
    return {"context": context, "execution_trace": state["execution_trace"]}
