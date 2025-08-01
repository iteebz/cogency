"""Embed services - auto-discovery."""

from .base import Embed
from .mistral import MistralEmbed
from .nomic import Nomic
from .openai import OpenAIEmbed
from .sentence import Sentence

__all__ = ["Embed", "MistralEmbed", "Nomic", "OpenAIEmbed", "Sentence"]
