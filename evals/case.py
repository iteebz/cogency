"""Test case types - zero ceremony."""

from dataclasses import dataclass


@dataclass
class Case:
    prompt: str
    criteria: str
    profile: bool = False
    empty_tools: bool = False
    chunks: bool = False


@dataclass
class Memory:
    store: str
    recall: str
    criteria: str
    chunks: bool = False


@dataclass
class Multi:
    prompts: list[str]
    criteria: str
    chunks: bool = False
