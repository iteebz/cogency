"""Direct step binding - no composition ceremony."""

from functools import partial

from .act import act
from .reason import reason
from .respond import respond
from .synthesize import synthesize
from .triage import triage


def _setup_steps(llm, tools, memory, identity, output_schema, config=None):
    """Compose steps with optional resilience and checkpointing."""
    from resilient_result import Retry

    from cogency.decorators import compose_step

    return {
        "triage": partial(triage, llm=llm, tools=tools, memory=memory),
        "reason": compose_step(
            partial(reason, llm=llm, tools=tools, memory=memory),
            config=config,
            checkpoint_name="reasoning",
            retry_policy=Retry.api(),
        ),
        "act": compose_step(
            partial(act, llm=llm, tools=tools),
            config=config,
            checkpoint_name="tool_execution",
            retry_policy=Retry.db(),
        ),
        "respond": partial(
            respond,
            llm=llm,
            tools=tools,
            memory=memory,
            identity=identity,
            output_schema=output_schema,
        ),
        "synthesize": partial(synthesize, memory=memory),
    }
