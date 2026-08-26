"""Embedding provider contracts and adapters."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from eduagent.llm.provider import OpenAICompatibleProvider


class EmbeddingProvider(Protocol):
    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


class OpenAIEmbeddingProvider:
    """Expose the provider's embedding endpoint through a narrow interface."""

    def __init__(self, provider: OpenAICompatibleProvider) -> None:
        self.provider = provider

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return self.provider.embed(texts)
