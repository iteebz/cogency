"""Test case types - zero ceremony."""

from dataclasses import dataclass, field


@dataclass
class Case:
    prompt: str
    criteria: str
    profile: bool = False
    empty_tools: bool = False
    chunks: bool = False


@dataclass
class Memory(Case):
    store: str = ""
    recall: str = ""

    def __post_init__(self):
        self.prompt = ""
        self.profile = True


@dataclass
class Multi(Case):
    prompts: list[str] = field(default_factory=list)

    def __post_init__(self):
        self.prompt = ""
