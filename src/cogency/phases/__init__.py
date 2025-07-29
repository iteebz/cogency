"""Clean phase imports - zero ceremony."""

from .act import Act
from .base import Phase
from .preprocess import Preprocess
from .reason import Reason
from .reasoning import parse_switch, prompt_reasoning, should_switch, switch_mode
from .respond import Respond

__all__ = [
    "Act",
    "Preprocess",
    "Reason",
    "Respond",
    "setup_phases",
    "Phase",
    "parse_switch",
    "should_switch",
    "switch_mode",
    "prompt_reasoning",
]


def setup_phases(llm, tools, memory, identity, output_schema):
    """Zero ceremony phase creation."""
    return {
        "preprocess": Preprocess(llm=llm, tools=tools, memory=memory, identity=identity),
        "reason": Reason(llm=llm, tools=tools, identity=identity),
        "act": Act(tools=tools),
        "respond": Respond(
            llm=llm,
            tools=tools,
            identity=identity,
            output_schema=output_schema,
        ),
    }
